import requests, time
from selenium.common import TimeoutException, WebDriverException, NoSuchElementException, NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from bcpkgfox import login_2fac


class Login2facmycena:
    def __init__(self, uf, sistema, advogado, token, maximo = 10):
        self.codes = None
        self._api = _ApiControll(uf, sistema, advogado, token)
        self.code_timeout = maximo
        self.uf = uf
        self.sistema = sistema
        self.advogado = advogado
        self.token = token

    def processar_codes(self):
        max_attempts = self.code_timeout
        five_attempts = 0
        ten_attempts = 0

        while five_attempts <= max_attempts:
            five_attempts += 1
            self.codes = self._api.listar_codigos_otp()
            if self.codes:
                print("Códigos obtidos com sucesso:")
                return self.codes
            else:
                print("Solicitando novo codigo.")
                self._api.solicitar_codigos_otp()
                time.sleep(5)
                while ten_attempts <=10:
                    ten_attempts += 1
                    self.codes = self._api.listar_codigos_otp()
                    if self.codes:
                        return self.codes
                    time.sleep(5)
        return None

    def login_eproc(self, driver, url, tipo_login="mysena"):
        login = _LoginEproc(driver, self._api, url, self.uf, self.sistema, self.advogado, self.token, tipo_login, self.processar_codes)
        login.login()
        return True

    def login_pje(self, driver, url, tipo_login="mysena"):
        login = _LoginPje(driver, self._api, url, self.uf, self.sistema, self.advogado, self.token, tipo_login,
                            self.processar_codes)
        login.login()
        return True

class _ApiControll:
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


class _LoginEproc:
    def __init__(self, driver, api, url_procurada, uf, sistema, advogado, token, tipo_login="mysena", processar_codes=None):
        self.driver = driver
        self.api = api
        self.uf = uf
        self.sistema = sistema
        self.advogado = advogado
        self.url_procurada = url_procurada
        self.tipo_login = tipo_login.lower if tipo_login else "mysena"
        self._util = _Utils(driver, api, url_procurada, uf, sistema, advogado, token,tipo_login)
        self.processar_codes = processar_codes

    def login(self):
        """
        Realiza o login no sistema EPROC.

        Prioridade:
        1. Verifica se já está logado
        2. Login via WHOM (para estados específicos: RJ, TO)
        3. Login via Certificado Digital + 2FA (método principal)
        """
        print(f"\n{'='*60}")
        print(f"[LOGIN] Acessando: {self.url_procurada}")
        print(f"{'='*60}")

        self.driver.get(f"{self.url_procurada}")
        time.sleep(2)

        # ══════════════════════════════════════════════════════════════
        # PRIORIDADE 1: Verifica se já está logado
        # ══════════════════════════════════════════════════════════════
        if self._verificar_ja_logado():
            return

        # ══════════════════════════════════════════════════════════════
        # PRIORIDADE 2: Login via WHOM (estados específicos)
        # ══════════════════════════════════════════════════════════════
        if self._util.deve_usar_whom():
            # Verifica se o login foi bem-sucedido
            self._util.login_via_whom()
            if self._confere_login_sucesso():
                print("  ✓ Login via WHOM realizado com sucesso!")
                self._finalizar_login()
                return True
            else:
                print("⚠ Login via WHOM falhou. Não há fallback disponível para este estado.")
                raise Exception("Falha no login via WHOM")



        # ══════════════════════════════════════════════════════════════
        # PRIORIDADE 3: Login via Certificado Digital + 2FA
        # ══════════════════════════════════════════════════════════════
        self._login_via_certificado_digital()

    def _verificar_ja_logado(self):
        """
        Verifica se o usuário já está logado no sistema.
        Retorna True se já está logado, False caso contrário.
        """
        print("\n[1/3] Verificando se já está logado...")

        response_login_sucesso = self._confere_login_sucesso()
        if response_login_sucesso:
            print("  ✓ Já estava logado no sistema.")
            self._finalizar_login()
            return True

        print("  → Usuário não está logado. Prosseguindo com autenticação...")
        return False

    def _confere_login_sucesso(self):
        """
        Verifica se o login foi bem-sucedido.
        Retorna False se encontrar elementos de login (usuário não está logado).
        Retorna True se não encontrar elementos de login (usuário está logado).
        """
        self._confere_e_aceita_popup_advogado_logado()

        try:
            # Tenta encontrar qualquer elemento que indique tela de login
            # Usando XPath com OR para cobrir múltiplas variações
            self._util.find_clickable_element_with_wait(By.XPATH, "//button[@id='kc-login-certificate'] | //input[@value='Certificado Digital'] | //input[contains(@onclick, 'SubmitCert')]", timeout=10)
            # Se encontrou algum elemento de login, significa que NÃO está logado
            return False
        except Exception:
            # Se não encontrou elementos de login, está logado
            return True

    def _login_via_certificado_digital(self, tentativa=1):
        """
        Realiza login via Certificado Digital + código 2FA.

        Fluxo:
        1. Clica no botão de Certificado Digital (se estiver na tela de login)
        2. Fica na tela de 2FA até conseguir logar
        3. Se der erro, recarrega a página e tenta novo código

        Args:
            tentativa: Número da tentativa atual (máximo 5)
        """
        max_tentativas = 5

        print(f"\n[LOGIN CERTIFICADO] Tentativa {tentativa}/{max_tentativas}")
        print("  → Método: Certificado Digital + 2FA")

        try:
            # ─────────────────────────────────────────────────────────
            # PASSO 1: Verificar estado atual da página
            # ─────────────────────────────────────────────────────────
            print("\n  [Passo 1/4] Verificando estado da página...")

            # Verifica se voltou para tela de login (usuário/senha)
            if self._esta_na_tela_login():
                print("    → Está na tela de login. Clicando em Certificado Digital...")
                btn_certificado = self._util.find_clickable_element_with_wait(
                    By.XPATH,
                    "//button[@id='kc-login-certificate'] | //input[@value='Certificado Digital'] | //input[contains(@onclick, 'SubmitCert')]",
                    timeout=20,
                )
                btn_certificado.click()
                print("    ✓ Botão Certificado Digital clicado")
                time.sleep(3)

                # Verifica se apareceu algum alert (erro de certificado)
                if self._tratar_alert_login(tentativa, max_tentativas):
                    return

            # Verifica erro de conexão
            if self._verificar_erro_conexao():
                if tentativa < max_tentativas:
                    return self._login_via_certificado_digital(tentativa + 1)
                else:
                    raise Exception("Erro de conexão persistente após múltiplas tentativas")

            # ─────────────────────────────────────────────────────────
            # PASSO 2: Verificar se já logou direto (sem 2FA)
            # ─────────────────────────────────────────────────────────
            print("\n  [Passo 2/4] Verificando se já está logado...")

            if self._verificar_login_sucesso_direto():
                print("    ✓ Login realizado sem necessidade de 2FA!")
                self._finalizar_login()
                return

            # ─────────────────────────────────────────────────────────
            # PASSO 3: Loop de tentativas de código 2FA
            # ─────────────────────────────────────────────────────────
            print("\n  [Passo 3/4] Entrando no loop de validação 2FA...")

            tentativas_2fa = 0
            max_tentativas_2fa = 5

            while tentativas_2fa < max_tentativas_2fa:
                tentativas_2fa += 1
                print(f"\n    [2FA] Tentativa {tentativas_2fa}/{max_tentativas_2fa}")

                # Verifica se voltou para tela de login (sessão expirou)
                if self._esta_na_tela_login():
                    print("    ⚠ Voltou para tela de login. Reiniciando processo...")
                    return self._login_via_certificado_digital(tentativa + 1)

                # Verifica se já está logado
                if self._verificar_login_sucesso_direto():
                    print("    ✓ Login bem-sucedido!")
                    self._finalizar_login()
                    return

                # Verifica se está na tela de 2FA
                if not self._esta_na_tela_2fa():
                    print("    ⚠ Não está na tela de 2FA. Recarregando página...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue

                # Obtém novo código 2FA
                code = self._obter_codigo_2fa()
                if not code:
                    print("    ✗ Falha ao obter código. Recarregando página...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue

                print(f"    ✓ Código 2FA obtido: {code[:2]}****")

                # Localiza e preenche o campo 2FA
                try:
                    campo_2fa = self._util.find_element_with_wait(
                        By.XPATH,
                        "//*[self::input[@id='txtAcessoCodigo'] or self::input[@id='otp']]",
                        timeout=10,
                    )
                    campo_2fa.clear()
                    campo_2fa.send_keys(code)
                    print("    ✓ Código inserido no campo")
                except TimeoutException:
                    print("    ✗ Campo 2FA não encontrado. Recarregando página...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue

                # ─────────────────────────────────────────────────────────
                # PASSO 4: Confirmar login
                # ─────────────────────────────────────────────────────────
                print("\n  [Passo 4/4] Confirmando login...")

                # Pressiona ENTER para confirmar
                campo_2fa.send_keys(Keys.ENTER)
                print("    ✓ ENTER pressionado para confirmar")

                time.sleep(3)

                # Verifica se apareceu alert após confirmar
                self._tratar_alert_login(tentativa, max_tentativas)

                # Verifica erro de 2FA (div de erro) - NÃO clica em cancelar, apenas recarrega
                if self._verificar_erro_2fa():
                    print("    → Recarregando página para tentar novo código...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue

                # Verifica se login foi bem-sucedido
                time.sleep(2)
                if self._verificar_login_sucesso_direto():
                    print("\n  ✓ Login via Certificado Digital realizado com sucesso!")
                    self._finalizar_login()
                    return

                # Verifica se voltou para tela de login
                if self._esta_na_tela_login():
                    print("    ⚠ Voltou para tela de login. Reiniciando processo...")
                    return self._login_via_certificado_digital(tentativa + 1)

                print("    ⚠ Login não confirmado. Tentando novo código...")

            # Esgotou tentativas de 2FA
            raise Exception(f"Falha no login após {max_tentativas_2fa} tentativas de 2FA")

        except TimeoutException as e:
            print(f"\n  ✗ Timeout durante login: {e}")
            if tentativa < max_tentativas:
                print(f"  → Tentando novamente ({tentativa + 1}/{max_tentativas})...")
                time.sleep(2)
                return self._login_via_certificado_digital(tentativa + 1)
            else:
                raise Exception("Falha no login: timeout aguardando elementos da página")

        except Exception as e:
            print(f"\n  ✗ Erro durante login: {e}")
            if tentativa < max_tentativas and "Alert" not in str(e):
                print(f"  → Tentando novamente ({tentativa + 1}/{max_tentativas})...")
                time.sleep(2)
                return self._login_via_certificado_digital(tentativa + 1)
            else:
                raise Exception(f"Falha no login via certificado: {e}")

    def _esta_na_tela_login(self):
        """
        Verifica se está na tela de login (usuário/senha).
        """
        try:
            self.driver.find_element(
                By.XPATH,
                "//button[@id='kc-login-certificate'] | //input[@value='Certificado Digital'] | //input[contains(@onclick, 'SubmitCert')]",
            )
            return True
        except NoSuchElementException:
            return False

    def _esta_na_tela_2fa(self):
        """
        Verifica se está na tela de inserção do código 2FA.
        """
        try:
            self.driver.find_element(By.XPATH, "//*[self::input[@id='txtAcessoCodigo'] or self::input[@id='otp']]")
            return True
        except NoSuchElementException:
            return False

    def _obter_codigo_2fa(self):
        """
        Obtém o código 2FA via API (login_2factor).
        Retorna o código ou None se falhar.
        """
        try:

            code = self.processar_codes()
            return code
        except Exception as e:
            print(f"    ✗ Erro ao obter código 2FA: {e}")
            return None

    def _tratar_alert_login(self, tentativa, max_tentativas):
        """
        Verifica e trata alerts que podem aparecer durante o login.

        Retorna:
            True se um alert foi tratado (e retry foi feito se necessário)
            False se não havia alert
        """
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"\n  ⚠ Alert detectado: {alert_text}")
            alert.accept()

            # Se for alert de login inválido, tenta novamente
            if "inválido" in alert_text.lower() or "Login []" in alert_text:
                if tentativa < max_tentativas:
                    print(f"  → Tentando login novamente ({tentativa + 1}/{max_tentativas})...")
                    time.sleep(2)
                    self._login_via_certificado_digital(tentativa + 1)
                    return True
                else:
                    raise Exception(f"Login falhou após {max_tentativas} tentativas: {alert_text}")

            return True

        except NoSuchElementException:
            return False
        except Exception as e:
            if "no such alert" in str(e).lower() or "no alert" in str(e).lower():
                return False
            raise

    def _verificar_erro_conexao(self):
        """
        Verifica se houve erro de conexão na página.
        Se detectar, faz refresh e retorna True.
        """
        page_source_lower = self.driver.page_source.lower()
        if "conexão interrompida" in page_source_lower or "connection interrupted" in page_source_lower:
            print("    ⚠ Conexão interrompida detectada, fazendo refresh...")
            self.driver.refresh()
            time.sleep(3)
            return True
        return False

    def _verificar_erro_2fa(self):
        """
        Verifica se apareceu erro de validação do código 2FA.
        Retorna True se erro detectado, False caso contrário.
        """
        try:
            div_erro = self.driver.find_element(By.ID, "divErro")
            if div_erro.is_displayed():
                texto_erro = div_erro.text
                print(f"    ⚠ Erro de 2FA detectado: {texto_erro}")
                return True
        except NoSuchElementException:
            pass
        return False

    def _verificar_login_sucesso_direto(self):
        """
        Verifica se o login foi feito diretamente (sem necessidade de 2FA).
        """
        page_source = self.driver.page_source
        indicadores_sucesso = ["Painel do Advogado", "Citações/Intimações", "Painel do usuário", "selInfraUnidades"]
        return any(indicador in page_source for indicador in indicadores_sucesso)

    def _finalizar_login(self):
        """
        Finaliza o processo de login verificando popups e seleção de perfil.
        """
        print("\n[FINALIZANDO LOGIN]")

        # Aceita popups se houver
        self._confere_e_aceita_popup_advogado_logado()

        # Verifica e seleciona perfil de advogado se necessário
        response_perfil = self._confere_tela_de_selecao_de_perfil()
        if response_perfil:
            print("  → Selecionando perfil de advogado...")
            self._selecionar_perfil_advogado()

        print("  ✓ Login finalizado com sucesso!\n")

    def _confere_tela_de_selecao_de_perfil(self):
        """
        Verifica se a tela de seleção de perfil está presente.
        """
        try:
            elemento_perfil = self._util.find_element_with_wait(By.XPATH, "//*[contains(text(), 'Seleção de perfil')]", 5)
            if elemento_perfil:
                return True
        except TimeoutException:
            if "Seleção de perfil" in self.driver.page_source:
                return True
            else:
                return False

    def _confere_e_aceita_popup_advogado_logado(self, refresh=False):
        """
        Função que busca um alerta na página e aceita o mesmo.
        """
        try:
            alert = WebDriverWait(self.driver, 5).until(ec.alert_is_present())
            alert.accept()
            time.sleep(1)
            if refresh:
                self.driver.refresh()
            return True
        except TimeoutException:
            return False
        except NoAlertPresentException:
            return False

    def _selecionar_perfil_advogado(self):
        """
        Seleciona o perfil de advogado na tela de seleção de perfil.
        """

        try:
            botao_advogado = self._util.find_element_with_wait(By.XPATH, "//button[@id='tr0']", 10)
            botao_advogado.click()
        except TimeoutException:
            forms_de_perfis = self._util.find_element_with_wait(By.XPATH, "//form[@id='frmEscolherUsuario']", 10)
            primeira_opcao = self._util.find_element_with_wait(By.XPATH, ".//button[contains(@id, 'tr0')]", 10,
                                                         parent=forms_de_perfis)
            primeira_opcao.click()

        return

class _LoginPje:
    def __init__(self, driver, api, url_procurada, uf, sistema, advogado, token, tipo_login="mysena", processar_codes=None):
        self.driver = driver
        self.api = api
        self.uf = uf
        self.sistema = sistema
        self.advogado = advogado
        self.url_procurada = url_procurada
        self.tipo_login = tipo_login.lower if tipo_login else "mysena"
        self._util = _Utils(driver, api, url_procurada, uf, sistema, advogado, token,tipo_login)
        self.processar_codes = processar_codes
        
    def login(self):
        """
        Realiza o login no sistema EPROC.

        Prioridade:
        1. Verifica se já está logado
        2. Login via WHOM (para estados específicos: RJ, TO)
        3. Login via Certificado Digital + 2FA (método principal)
        """
        print(f"\n{'='*60}")
        print(f"[LOGIN] Acessando: {self.url_procurada}")
        print(f"{'='*60}")

        self.driver.get(f"{self.url_procurada}")
        time.sleep(2)

        # ══════════════════════════════════════════════════════════════
        # PRIORIDADE 1: Verifica se já está logado
        # ══════════════════════════════════════════════════════════════
        if self._verificar_ja_logado():
            return True

        print(f"{self.url_procurada}")
        self.driver.get(f"{self.url_procurada}")
        self.driver.execute_script("document.body.style.zoom='90%'")

    
        el_peticionar = '//td[contains(@id,"tabExpedientes_lbl") or contains(text(),"Expedientes")]'
        time.sleep(1)
        if "EXPEDIENTES" in self.driver.page_source or "ciência" in self.driver.page_source or "Ciencia" in self.driver.page_source or "Selecione uma jurisdição ou caixa" in self.driver.page_source:
            print("Já logado, continuando o código.")
            if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
                self._util.find_element_with_wait(
                    By.XPATH,
                    '//td[contains(@id,"tabExpedientes_lbl")] or //td[contains(text(),"Expedientes")]',
                ).click()
    
            self._fechar_popup_certificado()
            return True
    
        if "Avisos" in self.driver.page_source or "Mensagens" in self.driver.page_source or "Painel do usuário" in self.driver.page_source:
            try:
                btn_painel = self._util.find_element_with_wait(By.XPATH, "//input[contains(@value, 'Painel do usuário')]")
                self.driver.execute_script("arguments[0].click();", btn_painel)
            except BaseException:
                if self._util.verificar_home_seam_atual():
                    link_redirect = self._util.find_element_with_wait(By.XPATH, "//a[contains(@href,'painel')]")
                    link_redirect = link_redirect.get_attribute("href")
                    self.driver.get(link_redirect)
                    time.sleep(2)
                    self._util.loading()
                else:
                    btn_painel = self._util.find_element_with_wait(By.XPATH, "//a[@id='home']")
                    self.driver.execute_script("arguments[0].click();", btn_painel)

            self._util.find_clickable_element_with_wait(By.XPATH, "//body", 30)
            print("Já logado, continuando o código.")
            if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
                self._util.find_element_with_wait(
                    By.XPATH,
                    '//td[contains(@id,"tabExpedientes_lbl")] or //td[contains(text(),"Expedientes")]',
                ).click()
                self._fechar_popup_certificado()
    
            return True
    
        elif "403 Forbidden" in self.driver.page_source:
            raise WebDriverException("Erro 403 Forbidden ao acessar o PJe.")
    
        xpath_framers = ["ssoFrame", "ifrmLogin", "framePeticionar"]
        text_quebra = "Número do processo"
        self._util.loading()
        time.sleep(2)
        self._util.framer_atached(
            xpath_framers=xpath_framers,
            text_quebra=text_quebra,
            el=el_peticionar,
            quebra=True,
        )
    
        xpath_cert = (
            "//input["
            "contains(@id, 'kc-pje-office') or "
            "contains(@name, 'login-pje-office') or "
            "contains(@value, 'CERTIFICADO DIGITAL') or "
            "contains(@id, 'loginAplicacaoButton') or "
            "contains(@name, 'loginAplicacaoButton') or "
            "contains(@value, 'Certificado Digital')"
            "]"
        )
    
        self._verificar_bad_request()
    
        try:
            click_certification = self._util.find_element_with_wait(By.XPATH, xpath_cert, timeout=30)
            if click_certification:
                if self._util.deve_usar_whom():
                    # Verifica se o login foi bem-sucedido
                    self._util.login_via_whom()
                    if self._verificar_ja_logado():
                        print("  ✓ Login via WHOM realizado com sucesso!")
                        return True
                    else:
                        print("⚠ Login via WHOM falhou. Não há fallback disponível para este estado.")
                        raise Exception("Falha no login via WHOM")
                else:
                    click_certification.click()
                    print("CLICOU NO CERTIFICADO DIGITAL")
    
            time.sleep(2)
            self._util.loading()
    
            self._verificar_bad_request()
            if self._verificar_ja_logado():
                return True

            #TODO ADICIONAR AREA DO OTP
            code = self._obter_codigo_2fa()
            if code:
                self._insert_codigo_2fa(code)
            else:
                self.login()

            self._fechar_popup_certificado()
            if "Redirecionamento em excesso por" in self.driver.page_source:
                self.driver.refresh()
                time.sleep(2)
                pass
    
            try:
                input_certificado = self.driver.find_elements(By.XPATH, xpath_cert)
                if input_certificado:
                    self.driver.refresh()
                    time.sleep(1)
                    click_certification = self._util.find_element_with_wait(By.XPATH, xpath_cert, timeout=30)
                    try:
                        self.driver.execute_script("arguments[0].click();", click_certification)
                    except Exception:
                        click_certification.click()
                    self._util.loading()
                    time.sleep(2)
            except NoSuchElementException:
                pass
    
        except Exception as e:
            print(f"Erro ao clicar no certificado digital ou já logado: {e}")
            self._fechar_popup_certificado()
            if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
                try:
                    self._util.find_element_with_wait(By.XPATH, f"{el_peticionar}").click()
                    self.driver.switch_to.default_content()
                except BaseException:
                    self.driver.switch_to.default_content()
                    self._util.find_element_with_wait(By.XPATH, f"{el_peticionar}").click()
                self._util.loading()
                time.sleep(0.5)
            else:
                self._util.framer_atached(xpath_framers, text_quebra, el_peticionar)
                self.driver.switch_to.default_content()
    
        self.driver.switch_to.default_content()
        time.sleep(2)
    
        if "Redirecionamento em excesso por" in self.driver.page_source:
            self.driver.refresh()
            time.sleep(2)
            pass
    
        self._util.framer_atached(xpath_framers, text_quebra, el_peticionar)
    
        if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
            try:
                self._util.find_element_with_wait(By.XPATH, f"{el_peticionar}", 5).click()
                self.driver.switch_to.default_content()
            except BaseException:
                self.driver.switch_to.default_content()
                self._util.find_element_with_wait(By.XPATH, f"{el_peticionar}").click()
            self._util.loading()
            time.sleep(0.5)
    
        self._fechar_popup_certificado()
    
        if "Sua página expirou, por favor tente novamente." in self.driver.page_source:
            self.driver.refresh()
            time.sleep(1)
            self.login()
            self._util.loading()
            return
    
        if "Avisos" in self.driver.page_source or "Mensagens" in self.driver.page_source or "Painel do usuário" in self.driver.page_source:
            try:
                btn_painel = self._util.find_element_with_wait(By.XPATH, "//input[contains(@value, 'Painel do usuário')]")
                self.driver.execute_script("arguments[0].click();", btn_painel)
            except BaseException:
                if self._util.verificar_home_seam_atual():
                    link_redirect = self._util.find_element_with_wait(By.XPATH, "//a[contains(@href,'painel')]")
                    link_redirect = link_redirect.get_attribute("href")
                    self.driver.get(link_redirect)
                    time.sleep(2)
                    self._util.loading()
                else:
                    btn_painel = self._util.find_element_with_wait(By.XPATH, "//a[@id='home']")
                    self.driver.execute_script("arguments[0].click();", btn_painel)
            self._util.find_clickable_element_with_wait(By.XPATH, "//body", 30)
            print("Já logado, continuando o código.")

            if "Sua página expirou, por favor tente novamente." in self.driver.page_source:
                self.driver.refresh()
                time.sleep(1)
                self.login()
                self._util.loading()
                return

            if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
                self._util.find_element_with_wait(
                    By.XPATH,
                    '//td[contains(@id,"tabExpedientes_lbl")] or //td[contains(text(),"Expedientes")]',
                ).click()
                self._fechar_popup_certificado()
    
        if self._util.verificar_home_seam_atual():
            link_redirect = self._util.find_element_with_wait(By.XPATH, "//a[contains(@href,'painel')]")
            link_redirect = link_redirect.get_attribute("href")
            self.driver.get(link_redirect)
            time.sleep(2)
            self._util.loading()
            return
        else:
            return

    def _verificar_ja_logado(self):
        if "Avisos" in self.driver.page_source or "Mensagens" in self.driver.page_source or "Painel do usuário" in self.driver.page_source:
            try:
                btn_painel = self._util.find_element_with_wait(By.XPATH,
                                                               "//input[contains(@value, 'Painel do usuário')]")
                self.driver.execute_script("arguments[0].click();", btn_painel)
            except BaseException:
                if self._util.verificar_home_seam_atual():
                    link_redirect = self._util.find_element_with_wait(By.XPATH, "//a[contains(@href,'painel')]")
                    link_redirect = link_redirect.get_attribute("href")
                    self.driver.get(link_redirect)
                    time.sleep(2)
                    self._util.loading()
                else:
                    btn_painel = self._util.find_element_with_wait(By.XPATH, "//a[@id='home']")
                    self.driver.execute_script("arguments[0].click();", btn_painel)

            self._util.find_clickable_element_with_wait(By.XPATH, "//body", 30)

            if "Sua página expirou, por favor tente novamente." in self.driver.page_source:
                self.driver.refresh()
                time.sleep(1)
                self.login()
                self._util.loading()
                return True

            if "Número do processo" in self.driver.page_source and "Quadro de avisos" not in self.driver.page_source:
                self._util.find_element_with_wait(
                    By.XPATH,
                    '//td[contains(@id,"tabExpedientes_lbl")] or //td[contains(text(),"Expedientes")]',
                ).click()
                self._fechar_popup_certificado()

            if self._util.verificar_home_seam_atual():
                link_redirect = self._util.find_element_with_wait(By.XPATH, "//a[contains(@href,'painel')]")
                link_redirect = link_redirect.get_attribute("href")
                self.driver.get(link_redirect)
                time.sleep(2)
                self._util.loading()
                return True
            else:
                return True
        else:
            return False

    def _fechar_popup_certificado(self):
        if "Certificado próximo de expirar" in self.driver.page_source:
            try:
                bt_fechar = self._util.find_element_with_wait(
                    By.XPATH,
                    "//span[contains(@class,'btn-fechar') or contains(@onclick,'fechar')]",
                )
                bt_fechar.click()
                self._util.loading()

            except BaseException:
                pass

    def _verificar_bad_request(self):
            if "Bad Request" in self.driver.page_source:
                raise WebDriverException("Erro de Bad Request ao acessar o PJe.")

    def _esta_na_tela_2fa(self):
        """
        Verifica se está na tela de inserção do código 2FA.
        """
        try:
            self.driver.find_element(By.XPATH, "//*[self::input[@id='txtAcessoCodigo'] or self::input[@id='otp']]")
            return True
        except NoSuchElementException:
            return False

    def _obter_codigo_2fa(self):
        """
        Obtém o código 2FA via API (login_2factor).
        Retorna o código ou None se falhar.
        """
        try:

            code = self.processar_codes()
            return code
        except Exception as e:
            print(f"    ✗ Erro ao obter código 2FA: {e}")
            return None

    def _insert_codigo_2fa(self,code):
        # Verifica se apareceu o formulário de autenticação 2FA
        try:
            if code:
                input_otp = self._util.find_element_with_wait(By.XPATH,
                                                              "//form[@id='kc-otp-login-form'] | //input[@id='otp' and @name='otp']",
                                                              timeout=5)
                if input_otp:
                    input_otp = self._util.find_element_with_wait(By.XPATH, "//input[contains(@type,'text')]")
                    time.sleep(2)

                input_otp.clear()
                input_otp.send_keys(str(code))

                click_validar = self._util.find_element_with_wait(By.XPATH,
                                                                  "//input[contains(@type,'submit')] | //button[contains(@type,'submit')]",
                                                                  timeout=5)
                click_validar.click()
                self._util.loading()
                if 'Código inválido'.lower() in self.driver.page_source.lower():
                    code = self._obter_codigo_2fa()
                    self._insert_codigo_2fa(code)
                    return
            else:
                self.login()
        except (TimeoutException, NoSuchElementException):
            # Formulário OTP não apareceu, continua normalmente
            pass
class _Utils:
    def __init__(self, driver, api, url_procurada, uf, sistema, advogado, token, tipo='mysena'):
        self.driver = driver
        self.tipo_login = tipo
        self.sistema = sistema
        self.advogado = advogado
        self.token = token
        self.url_procurada = url_procurada
        self.uf = uf
        self.api = api

    def find_element_with_wait(self, by, value, timeout=10, parent=None):
        if parent is None:
            parent = self.driver  # Usa o driver principal se nenhum elemento pai for passado
        return WebDriverWait(parent, timeout).until(ec.presence_of_element_located((by, value)))

    def find_elements_with_wait(self, by, value, timeout=10, parent=None):
        if parent is None:
            parent = self.driver  # Usa o driver principal se nenhum elemento pai for passado
        return WebDriverWait(parent, timeout).until(ec.presence_of_all_elements_located((by, value)))

    def find_clickable_element_with_wait(self, by, value, timeout=10, parent=None):
        if parent is None:
            parent = self.driver  # Usa o driver principal se nenhum elemento pai for passado
        return WebDriverWait(parent, timeout).until(ec.element_to_be_clickable((by, value)))

    def deve_usar_whom(self):
        """
        Determina se deve usar o login via WHOM baseado no estado (UF).
        Estados que usam WHOM: RJ, TO
        """
        if self.tipo_login.lower() == "mysena" or "my" in self.tipo_login.lower():
            return False
        elif 'whoom' in self.tipo_login.lower() or self.tipo_login.lower() == 'whoom' or self.tipo_login.lower() == 'whom' or self.tipo_login.lower() == 'wh' or 'wh' in self.tipo_login.lower() :
            return True
        else:
            return False

    def login_via_whom(self):
        """
        Realiza login via WHOM (login_2fac do bcpkgfox).
        Todo o processo de autenticação é feito pela função login_2fac.

        Retorna True se login bem-sucedido, False caso contrário.
        """
        print(f"\n[LOGIN WHOM] Iniciando login via WHOM para {self.uf}...")
        print(f"  → Sistema: {self.sistema}")
        print(f"  → Certificado: {self.advogado}")

        try:
            login_2fac(
                driver=self.driver,
                certificate=f"{self.advogado}",
                system=f"{self.sistema}",
                token=f"{self.token}",
                code_timeout=120,
            )
            time.sleep(3)
        except Exception as e:
            print(f"  ✗ Erro durante login via WHOM: {e}")
            return False

    def framer_atached(self, xpath_framers, quebra=False, text_quebra="", el=""):
        for framer in xpath_framers:
            try:
                self.driver.switch_to.frame(framer)
                if quebra:
                    if framer == "framePeticionar":
                        if f"{text_quebra}" in self.driver.page_source:
                            try:
                                self.find_element_with_wait(By.XPATH, f"{el}").click()
                            except BaseException:
                                self.driver.switch_to.default_content()
                                self.find_element_with_wait(By.XPATH, f"{el}").click()
                            return
                break
            except NoSuchElementException:
                continue
            except BaseException:
                continue

    def loading(self):
        timeout = 60  # Tempo máximo de espera em segundos
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                print("Aviso: A verificação de 'loading' excedeu o tempo limite.")
                break
            try:
                styled = self.driver.find_element("xpath", '//*[@id="_viewRoot:status.start"]')
                style_content = styled.get_attribute("style")
                if "display: none;" in style_content:
                    break  # Sai do loop se o carregamento terminou
                else:
                    time.sleep(0.5)  # Espera um pouco antes de verificar novamente
            except NoSuchElementException:
                break  # Sai do loop se o elemento de loading não for encontrado

    def verificar_home_seam_atual(self):
        """
        Verifica se 'home.seam' está presente na URL atual do navegador.
        """
        url_atual = self.driver.current_url
        if "home.seam" in url_atual:
            print(f"'home.seam' encontrado na URL atual: {url_atual}")
            return True
        else:
            print(f"'home.seam' NÃO encontrado na URL atual: {url_atual}")
            return False

    def msg_aviso(self, mensagem, titulo="Aviso"):
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(titulo, mensagem, parent=root)
        root.destroy()