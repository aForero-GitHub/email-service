# core/circuit_breaker.py
import pybreaker

# Configuración de circuit breakers
sendgrid_circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)
ses_circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60)

def get_circuit_breakers():
    return {
        "SendGrid": sendgrid_circuit_breaker,
        "Amazon SES": ses_circuit_breaker
    }
