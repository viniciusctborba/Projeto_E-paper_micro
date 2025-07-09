# 📘 Projeto E-Paper Micro

Dashboard interativo em papel eletrônico (e-paper), desenvolvido para exibir informações úteis de forma clara, conectada e de baixo consumo energético.

## 💡 Descrição

Este projeto consiste em um **dashboard informativo** exibido em uma tela **e-paper** controlada por um **ESP32-S3**. Ele é capaz de exibir diversos tipos de dados em tempo real, utilizando diferentes APIs e serviços. A interface é atualizada de acordo com filtros definidos pelo usuário e pode ser interagida com botões físicos.

A caixa que abriga o hardware foi modelada no **Onshape** e impressa em **3D**, garantindo portabilidade e estética.

---

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

- Caixa impressa em 3D projetada no [**Onshape**](https://www.onshape.com/)
https://cad.onshape.com/documents/d5bf3e8aec9efe74c95e4767/w/c13b762c255baec64c60f23f/e/00f9ddf429701c9acd36b891?renderMode=0&uiState=68658c0a88b15d56732ca4c4
![image](https://github.com/user-attachments/assets/9010bae8-edba-41b9-8cd1-254abb99af8d
visao traseira


![image](https://github.com/user-attachments/assets/695102de-1351-43e3-b82e-363d3446b188)
visao frontal


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
