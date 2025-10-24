# Instalação da Detecção de Código de Barras

O sistema usa a biblioteca `pyzbar` para detectar códigos de barras como fallback quando o QR code não é detectado.

## Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y libzbar0
```

## Windows

### Opção 1: Usando chocolatey (recomendado)
```powershell
choco install zbar
```

### Opção 2: Download manual
1. Baixe o instalador do zbar: http://zbar.sourceforge.net/
2. Ou baixe diretamente: https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe/download
3. Execute o instalador
4. Adicione o caminho ao PATH do Windows (exemplo: `C:\Program Files (x86)\ZBar\bin`)

### Opção 3: Usar DLL diretamente
1. Baixe a DLL compilada: https://github.com/NaturalHistoryMuseum/pyzbar/releases
2. Coloque os arquivos DLL na pasta do projeto ou em `C:\Windows\System32`

## macOS

```bash
brew install zbar
```

## Verificar Instalação

Após instalar, teste se funciona:

```bash
python -c "from pyzbar import pyzbar; print('✓ pyzbar funcionando!')"
```

## Nota Importante

O sistema **continua funcionando** mesmo sem o zbar instalado! Ele simplesmente:
- Tenta detectar QR code primeiro (sempre funciona)
- Se o zbar estiver instalado, tenta código de barras como fallback
- Se o zbar NÃO estiver instalado, pula a detecção de código de barras silenciosamente

Nenhum erro será exibido se o zbar não estiver disponível.
