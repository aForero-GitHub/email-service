# email-service
In this repository you will find a project dedicated to optimize the workloads between two email providers, a very interesting project that mixes technologies such as serverless framework, python and redis.

## Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway as Amazon API Gateway
    participant sendEmail as Lambda sendEmail
    participant SQS as Amazon SQS (ColaCorreos)
    participant processEmailQueue as Lambda processEmailQueue
    participant email_service as Python EmailService
    participant Redis as Redis Cache
    participant SES as Amazon SES
    participant SendGrid as SendGrid

    Client->>APIGateway: Request to send email
    APIGateway->>sendEmail: Forward request
    sendEmail->>SQS: Send email data to SQS queue
    sendEmail->>Client: Return success response

    processEmailQueue->>SQS: Fetch email data from SQS
    processEmailQueue->>email_service: Pass email data to EmailService

    email_service->>Redis: Check provider usage and health
    Redis-->>email_service: Return provider usage and health

    alt Send with SendGrid
        email_service->>SendGrid: Attempt to send email
        SendGrid-->>email_service: Email sent successfully
        email_service->>Redis: Update metrics and mark SendGrid as healthy
    else Send with SES
        email_service->>SES: Attempt to send email
        SES-->>email_service: Email sent successfully
        email_service->>Redis: Update metrics and mark SES as healthy
    end

    email_service->>processEmailQueue: Return success status
    processEmailQueue->>CloudWatch: Log processing results
```
### Sequence Diagram Explanation

This sequence diagram represents the flow of an email request through a serverless architecture, detailing the interactions between the client, AWS services, and external email providers.

1. **Client Request**:
   - The client sends a request to send an email, which is received by the **Amazon API Gateway**.

2. **Forwarding to Lambda**:
   - The **API Gateway** forwards the email request to the **Lambda function sendEmail**.

3. **Queueing the Email**:
   - The **sendEmail** function processes the request and places the email data into **Amazon SQS (ColaCorreos)**, a message queue.
   - After the message is queued, **sendEmail** sends a success response back to the **Client**, indicating that the request was processed successfully.

4. **Processing the Queue**:
   - The **Lambda function processEmailQueue** retrieves the email data from **SQS**.
   - This email data is then passed to the **Python EmailService**, which handles the email dispatch logic.

5. **Provider Selection and Health Check**:
   - The **EmailService** interacts with **Redis** to check the usage history and health status of the available email providers (e.g., SendGrid and Amazon SES).
   - **Redis** returns the usage and health information to help determine which provider to use.

6. **Sending the Email**:
   - The **EmailService** attempts to send the email using one of the two providers:
     - **SendGrid**: If chosen, the email is sent via **SendGrid**, and success is confirmed. The metrics for **SendGrid** are updated in **Redis**, and the provider is marked as healthy.
     - **Amazon SES**: Alternatively, if **SES** is chosen, the email is sent via **SES**, and the success is logged in the same way as **SendGrid**.

7. **Logging the Result**:
   - After the email is successfully sent, the **EmailService** returns a success status to **processEmailQueue**.
   - The **processEmailQueue** function then logs the results of the email processing in **Amazon CloudWatch** for monitoring and diagnostics.

This architecture ensures that if one email provider fails, the system can quickly switch to the other provider without affecting the user experience. The use of Redis to track provider health and usage ensures that the system selects the optimal provider based on performance and reliability metrics.
