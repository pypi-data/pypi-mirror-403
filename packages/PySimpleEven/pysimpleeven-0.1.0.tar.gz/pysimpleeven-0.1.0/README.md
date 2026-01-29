# 🔢 PySimpleEven

**PySimpleEven** é uma biblioteca Python minimalista projetada com um único propósito: verificar se um número é par ou ímpar. Ideal para quem busca uma implementação limpa, seguindo os padrões modernos de empacotamento (`src` layout).

## 🛠️ Funcionalidades

* Verificação lógica de números pares.


* Suporte para instalação via `pip` através de `setup.cfg` e `pyproject.toml`.


* Estrutura pronta para testes unitários com `pytest`.



## 📂 Estrutura do Repositório

O projeto está organizado da seguinte forma:

* `src/PySimpleEven/`: Contém o código-fonte principal.


* `is_even.py`: Arquivo com a lógica de verificação.




* `test_is_even.py`: Conjunto de testes para garantir a integridade da função.


* `pyproject.toml` & `setup.cfg`: Arquivos de configuração e metadados para build do pacote.


* `requirements.txt`: Lista de dependências do projeto.



## 🚀 Como Instalar

Para instalar o projeto em modo de desenvolvimento (editável), execute:

```bash
pip install -e .

```

Ou instale as dependências listadas:

```bash
pip install -r requirements.txt

```

## 💻 Exemplo de Uso

A função principal pode ser importada do módulo `is_even` localizado dentro do pacote `PySimpleEven`.

```python
from PySimpleEven.is_even import is_even

# Exemplo rápido
print(is_even(10)) # Retorna True
print(is_even(7))  # Retorna False

```

## 🧪 Rodando os Testes

Para validar as funções, você pode executar o arquivo de teste incluído no diretório raiz:

```bash
python -m pytest test_is_even.py

```

---

### 📝 Notas de Versão

O projeto utiliza o layout de diretório `src/`, o que ajuda a evitar importações acidentais do código local em vez do pacote instalado, uma prática recomendada pela comunidade Python.
