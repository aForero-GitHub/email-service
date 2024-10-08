import logging as logger
import time
import pybreaker
from ..core import RedisHandler
from ..core import get_circuit_breakers
from .sendgrid_service import SendGridService
from .ses_service import SESService
from ..models import EmailRequest
from ..core.config import LATENCY_THRESHOLD, LATENCY_HISTORY_SIZE, MAX_CONSECUTIVE_USE, USE_TRACKER_KEY, EMAIL_COUNT_KEY, HEALTH_CHECK_KEY, LATENCY_KEY


logger.basicConfig(level=logger.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',  
                    datefmt='%Y-%m-%d %H:%M:%S', 
                    handlers=[logger.StreamHandler()])


class EmailService:

    def __init__(self):
        self.sendgrid_service = SendGridService()
        self.ses_service = SESService()
        self.providers = [
            ("SendGrid", self.sendgrid_service),
            ("Amazon SES", self.ses_service)
        ]
        self.circuit_breakers = get_circuit_breakers()

    def send_email(self, email_data: EmailRequest, max_retries=2):
        """
        Envía un correo electrónico utilizando el proveedor más adecuado basado en el uso y la latencia.
        """
        current_provider = self.choose_provider_based_on_usage()

        for _ in range(max_retries):
            provider_name, provider_service = current_provider
            circuit_breaker = self.circuit_breakers[provider_name]

            if not self.is_provider_healthy(provider_name):
                current_provider = self.get_next_healthy_provider(provider_name)
                continue

            try:
                self.attempt_send_email(provider_name, provider_service, circuit_breaker, email_data)
                return provider_name  # Retornar si el envío fue exitoso

            except pybreaker.CircuitBreakerError:
                self.handle_circuit_breaker_error(provider_name)
                current_provider = self.get_next_healthy_provider(provider_name)
            except Exception as e:
                self.handle_general_exception(provider_name, e)
                current_provider = self.get_next_healthy_provider(provider_name)

        raise RuntimeError("Error al enviar el correo después de múltiples reintentos.")

    def choose_provider_based_on_usage(self):
        """
        Elige el proveedor basado en el uso y la latencia.
        """
        sendgrid_count = self.get_usage_count("SendGrid")
        ses_count = self.get_usage_count("Amazon SES")

        if self.should_switch_provider(sendgrid_count, "Amazon SES"):
            return self.providers[1]  # Switch to Amazon SES

        if self.should_switch_provider(ses_count, "SendGrid"):
            return self.providers[0]  # Switch to SendGrid

        return self.choose_provider_with_lower_latency()

    def get_next_healthy_provider(self, current_provider) -> str:
        """
        Obtiene el siguiente proveedor saludable.
        """
        for provider in self.providers:
            if provider[0] != current_provider and self.is_provider_healthy(provider[0]):
                logger.info(f"Cambiando a {provider[0]}, ya que es saludable.")
                return provider
        logger.error("No hay proveedores saludables disponibles.")
        raise RuntimeError("No hay proveedores saludables disponibles.")

    def log_provider_latencies(self) -> None:
        """
        Muestra las latencias actuales de los proveedores desde Redis.
        """
        sendgrid_latency = RedisHandler.get_predicted_latency("SendGrid", LATENCY_KEY)
        ses_latency = RedisHandler.get_predicted_latency("Amazon SES", LATENCY_KEY)
        logger.info(f"Latencias actuales en Redis -> SendGrid: {sendgrid_latency:.2f}s, Amazon SES: {ses_latency:.2f}s")

    def is_provider_healthy(self, provider_name) -> bool:
        """
        Verifica si el proveedor está saludable.
        """
        if not RedisHandler.is_provider_healthy(provider_name, HEALTH_CHECK_KEY):
            logger.warning(f"Proveedor {provider_name} marcado como no saludable. Cambiando de proveedor.")
            return False
        return True

    def attempt_send_email(self, provider_name, provider_service, circuit_breaker, email_data) -> None:
        """
        Intenta enviar el correo electrónico utilizando el proveedor y el circuito breaker.
        """
        start_time = time.time()
        logger.info(f"Intentando enviar con {provider_name}")
        print(f"Intentando enviar con {provider_name}")

        circuit_breaker.call(
            provider_service.send_email,
            to=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            from_email=email_data.from_email
        )

        latency = time.time() - start_time
        logger.info(f"Correo enviado exitosamente con {provider_name} en {latency:.2f} segundos.")
        self.update_provider_metrics(provider_name, latency)

    def update_provider_metrics(self, provider_name:str, latency:float) -> None:
        """
        Actualiza las métricas del proveedor en Redis.
        """
        RedisHandler.cache_latency(provider_name, latency, LATENCY_KEY, LATENCY_HISTORY_SIZE)
        RedisHandler.increment_email_count(provider_name, EMAIL_COUNT_KEY)
        self.log_provider_latencies()

        if latency > LATENCY_THRESHOLD:
            logger.warning(f"Latencia de {provider_name} excedió el umbral de {LATENCY_THRESHOLD} segundos.")
            RedisHandler.mark_provider_unhealthy(provider_name, HEALTH_CHECK_KEY)
            logger.info(f"{provider_name} marcado como no saludable debido a alta latencia.")
        else:
            RedisHandler.mark_provider_healthy(provider_name, HEALTH_CHECK_KEY)
            logger.info(f"{provider_name} marcado como saludable.")

        RedisHandler.track_provider_usage(provider_name, USE_TRACKER_KEY)
        logger.info(f"Uso del proveedor {provider_name} registrado en Redis.")

    def handle_circuit_breaker_error(self, provider_name) -> None:
        """
        Maneja el error del circuito breaker.
        """
        logger.warning(f"Circuito abierto para {provider_name}. Cambiando a otro proveedor.")
        RedisHandler.mark_provider_unhealthy(provider_name, self.HEALTH_CHECK_KEY)

    def handle_general_exception(self, provider_name, exception) -> None:
        """
        Maneja excepciones generales durante el envío del correo.
        """
        logger.error(f"Error al enviar con {provider_name}: {exception}")
        RedisHandler.mark_provider_unhealthy(provider_name, HEALTH_CHECK_KEY)

    def get_usage_count(self, provider_name) -> int:
        """
        Obtiene el conteo de uso del proveedor desde Redis.
        """
        return int(RedisHandler.get_usage_count(provider_name, USE_TRACKER_KEY) or 0)

    def should_switch_provider(self, usage_count, other_provider_name) -> bool:
        """
        Determina si se debe cambiar de proveedor basado en el uso y la salud del otro proveedor.
        """
        if usage_count >= MAX_CONSECUTIVE_USE:
            if RedisHandler.is_provider_healthy(other_provider_name, HEALTH_CHECK_KEY):
                logger.info(f"{other_provider_name} ha alcanzado el límite de uso consecutivo. Cambiando a {other_provider_name}.")
                return True
        return False

    def choose_provider_with_lower_latency(self) -> str:
        """
        Elige el proveedor con la menor latencia.
        """
        sendgrid_latency = RedisHandler.get_predicted_latency("SendGrid", LATENCY_KEY)
        ses_latency = RedisHandler.get_predicted_latency("Amazon SES", LATENCY_KEY)
        
        logger.info(f"Latencia SendGrid: {sendgrid_latency:.2f} segundos, Latencia Amazon SES: {ses_latency:.2f} segundos")

        return self.providers[0] if sendgrid_latency <= ses_latency else self.providers[1]