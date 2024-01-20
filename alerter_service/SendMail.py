import httpx
import asyncio

async def SendMail(async_client, address, sender, recipient, title, data, api_key, secret_key):
    """Funkcja rzuci wyjątek, jeśli otrzymamy kod odpowiedzi inny niż 2xx"""
    (sender_email, sender_name) = sender
    (recipient_email, recipient_name) = recipient
    headers = {'Content-Type': 'application/json'}
    data = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": sender_name
                },
                "To": [
                    {
                        "Email": recipient_email,
                        "Name": recipient_name
                    }
                ],
                "Subject": title,
                "TextPart": data,
            }
        ]
    }
    r = await async_client.post(address, json = data, headers = headers, auth = (api_key, secret_key))
    r.raise_for_status()

# Main pokazujący sposób użycia
async def main():
    # Co do adresu mailowego nadawcy, to chyba musimy używać mojego. Idk, czy mailjet robi o to problem,
    # Ale też nie mamy za bardzo alternatyw.
    sender = ("a.stalke@student.uw.edu.pl", "Andrzej Stalke TEST ALERTU")
    recipient = ("XXX", "XXXX")
    title = "TEST"
    text = "To jest czwarty test alertu"
    # Raczej tych dwóch niżej nie wsadza się na gita xD
    api_key = "Pan Tadeusz wszedł pierwszy, drżącymi rękami"
    secret_key = "Drzwi za sobą zamyka, och! Nareszcie sami."
    # O ile dobrze rozumiem, to httpx zaleca by client nie był ciągle tworzony od nowa dla kolejnych wiadomości
    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            SendMail(client, "https://api.mailjet.com/v3.1/send", sender, recipient, title + "5", text, api_key, secret_key),
            SendMail(client, "https://api.mailjet.com/v3.1/send", sender, recipient, title + "6", text, api_key, secret_key)
        )

if __name__ == "__main__":
    asyncio.run(main())
