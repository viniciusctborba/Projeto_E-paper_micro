# 📘 Projeto E-Paper Micro

Dashboard interativo em papel eletrônico, composto por duas partes distintas:

1. **Coletor de dados (Python)**  
   Executado em um dispositivo ou servidor à parte, utiliza APIs para coletar:
   - Previsão do tempo (Meteoblue)
   - Notícias (NewsAPI)
   - E‑mails filtrados 
   - Eventos da agenda
   - Posts de subreddits (via Reddit API)

   Esses dados são enviados como JSON via *serial* através do **MQTT**.

2. **Controlador de exibição (Arduino)**  
   Executado no **ESP32-S3**, recebe os JSONs via serial e renderiza na tela **e-paper 4.2"** usando um sketch em C++/Arduino.

A caixa foi modelada no **Onshape** e impressa em **3D** para integrar os componentes.
--

## 🚀 Funcionalidades

O dashboard exibe as seguintes informações:

- **📅 Agenda**  
  Consulta eventos futuros e em andamento, com base em filtros personalizados do usuário.

- **📨 E-mails**  
  Acessa a conta de e-mail logada para exibir os últimos e-mails, conforme critérios definidos, e registra continuamente novos e-mails recebidos.

- **🌤️ Previsão do Tempo**  
  Mostra as condições climáticas atuais e previsão futura utilizando a **API da Meteoblue**.

- **📰 Notícias**  
  Busca as últimas manchetes com base em palavras-chave e tópicos de interesse do usuário, usando a **NewsAPI**.

- **👾 Subreddits**  
  Realiza buscas nos subreddits definidos pelo usuário, filtrando por data e popularidade, via **Reddit API**.

---

## 🔌 Hardware Utilizado

- **ESP32-S3**  
  Microcontrolador com conectividade Wi-Fi e Bluetooth, ideal para aplicações IoT.

- **Tela E-Paper 4.2" (React Studios)**  
  Tela monocromática de baixo consumo energético, ideal para exibição contínua de dados.

- **Protoboard**

- **2 Botões Físicos**  
  Utilizados para navegação/interação com o dashboard.

- **1 Buzzer**  
  Para notificações sonoras.

---

## 🔧 Estrutura Física

- Caixa impressa em 3D projetada no [**Onshape**](https://cad.onshape.com/documents/d5bf3e8aec9efe74c95e4767/w/c13b762c255baec64c60f23f/e/00f9ddf429701c9acd36b891?renderMode=0&uiState=68658c0a88b15d56732ca4c4)


![image](https://github.com/user-attachments/assets/cc7367f9-35d9-4bbc-bacc-a0a8fd7aee2e)

foto

- Design compacto e funcional, com espaço para todos os componentes e acesso aos botões.

---

## 🧠 APIs Utilizadas

| Serviço       | Função                                 |
|---------------|----------------------------------------|
| Meteoblue     | Previsão do tempo                      |
| NewsAPI       | Consulta de notícias                   |
| Reddit API    | Busca em subreddits                    |
| Gmail API     | Consulta de e-mails                    |
| Google Calendar API | Consulta de eventos da agenda |

---
## ⚙️ Hardware

![image](https://github.com/user-attachments/assets/52820cd5-343a-42df-9ebd-8fa8412ee668)

esquema de montagem feito no Fritzing
