# core/redis_handler.py
import redis
from statistics import median
from ..core.config import REDIS_URL
import os

# Asegúrate de que la URL tenga el esquema correcto
redis_url = os.getenv("REDIS_URL", REDIS_URL)

# Conectar a Redis utilizando la URL
redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

class RedisHandler:
    
    @staticmethod
    def cache_latency(provider_name, latency, key, history_size):
        """
        Almacena la latencia de un proveedor en Redis.
        """
        redis_client.lpush(f"{key}:{provider_name}", latency)
        redis_client.ltrim(f"{key}:{provider_name}", 0, history_size - 1)

    @staticmethod
    def get_predicted_latency(provider_name, key):
        """
        Recupera la latencia media de un proveedor.
        """
        latencies = redis_client.lrange(f"{key}:{provider_name}", 0, -1)
        if not latencies:
            return float('inf')
        return median([float(latency) for latency in latencies])

    @staticmethod
    def increment_email_count(provider_name, count_key):
        """
        Incrementa el contador de correos enviados por proveedor.
        """
        redis_client.hincrby(count_key, provider_name, 1)

    @staticmethod
    def track_provider_usage(provider_name, use_tracker_key):
        """
        Aumenta el uso de un proveedor y resetea el otro.
        """
        redis_client.hincrby(use_tracker_key, provider_name, 1)
        other_provider = "Amazon SES" if provider_name == "SendGrid" else "SendGrid"
        redis_client.hset(use_tracker_key, other_provider, 0)

    @staticmethod
    def get_usage_count(provider_name, use_tracker_key):
        """
        Obtiene el conteo de uso consecutivo del proveedor desde Redis.
        """
        return redis_client.hget(use_tracker_key, provider_name) or 0

    @staticmethod
    def mark_provider_unhealthy(provider_name, health_key):
        redis_client.hset(health_key, provider_name, "unhealthy")

    @staticmethod
    def mark_provider_healthy(provider_name, health_key):
        redis_client.hset(health_key, provider_name, "healthy")

    @staticmethod
    def is_provider_healthy(provider_name, health_key):
        return redis_client.hget(health_key, provider_name) != "unhealthy"
