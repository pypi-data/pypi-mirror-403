import requests, time

class Login2facmycena:
    def __init__(self, uf, sistema, advogado, token, maximo = 5):
        self.codes = None
        self.api = ApiControll(uf, sistema, advogado, token)
        self.code_timeout = maximo

    def processar_codes(self):
        max_attempts = self.code_timeout
        five_attempts = 0
        ten_attempts = 0

        while five_attempts <= max_attempts:
            five_attempts += 1
            self.codes = self.api.listar_codigos_otp()
            if self.codes:
                print("Códigos obtidos com sucesso:")
                return self.codes
            else:
                print("Solicitando novo codigo.")
                self.api.solicitar_codigos_otp()
                time.sleep(10)
                while ten_attempts <=10:
                    ten_attempts += 1
                    self.codes = self.api.listar_codigos_otp()
                    if self.codes:
                        return self.codes
                    time.sleep(10)
                return None
        return None


class ApiControll:
        def __init__(self, uf, sistema, advogado, tk):
            super().__init__()
            self.uf = uf
            self.sistema = sistema
            self.advogado = advogado
            self.token = tk


        def solicitar_codigos_otp(self):
            url = "https://api-4.bcfox.com.br/bcjur/views/codigos-otp"
            headers = {
                "x-access-token": self.token,
                "Content-Type": "application/json"
            }

            payload = {
                "uf": self.uf,
                "advogado": self.advogado,
                "sistema": self.sistema
            }

            for tentativa in range(1, 6):
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)

                    if response.status_code == 200:
                        print(
                            f"Tentativa {tentativa}: Requisição bem-sucedida. Código de status: {response.status_code}")
                        response_data = response.json()
                        print(response_data)
                        return response_data
                    else:
                        print(f"Tentativa {tentativa}: Erro na requisição. Código de status: {response.status_code}")

                except requests.RequestException as e:
                    print(f"Tentativa {tentativa}: Ocorreu um erro na requisição: {e}")

                time.sleep(1)

            return None

        def listar_codigos_otp(self):
            url = f"https://api-4.bcfox.com.br/bcjur/views/codigos-otp/robo/{self.uf}/{self.sistema}/{self.advogado}"
            headers = {"x-access-token": self.token}

            # Retries authenticated OTP code listing on failure
            for tentativa in range(1, 6):
                try:
                    response = requests.get(url, headers=headers, timeout=30)

                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data:
                            return response_data[0].get("CODIGO_OTP")

                    else:
                        print(f"Tentativa {tentativa}: Status {response.status_code}")

                except requests.RequestException as e:
                    print(f"Tentativa {tentativa}: Erro na requisição: {e}")

                time.sleep(1)
            return None


