# ChromeDriver Manager

Um gerenciador simples e eficiente para manter o **ChromeDriver** sincronizado com a versão do **Google Chrome** instalada no Windows.

Ideal para automações com Selenium que quebram frequentemente devido a atualizações automáticas do navegador.

## 🚀 Funcionalidades

- **Detecção Automática:** Verifica a versão exata do Chrome instalado via Registro do Windows ou WMIC.
- **Verificação de Compatibilidade:** Compara com a versão do driver atual.
- **Download Inteligente:** Busca a versão correta (`Known Good Versions`) na API oficial do Google Chrome Labs.
- **Instalação Automática:** Baixa, descompacta e configura o executável do driver pronto para uso.

## 📋 Pré-requisitos

- Sistema Operacional: **Windows**/**Linux**.
- Python **3.13+**.

## 📦 Instalação

### Via pip
```bash
pip install chromedriver-version-manager
```