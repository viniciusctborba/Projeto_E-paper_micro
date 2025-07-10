# --- Importação de bibliotecas necessárias ---
import customtkinter as ctk  # Biblioteca para interfaces modernas baseadas em tkinter
import json  # Manipulação de arquivos JSON
import os  # Operações com o sistema de arquivos
from tkinter import messagebox  # Caixas de diálogo do tkinter
from auth_service import autenticar_gmail  # Função de autenticação personalizada

# --- Configurações e variáveis globais ---

# Dicionário que mapeia os nomes dos widgets para seus rótulos
WIDGETS = {
    'Clima': '☀️ Clima',
    'Email': '✉️ Email',
    'Notícias': '📰 Notícias',
    'Eventos': '📅 Eventos',
    'Reddit': '👽 Reddit'
}

# Cores personalizadas para manter a identidade visual
COLOR_CANVAS = "#243763"  # Cor de fundo da tela principal
COLOR_CANVAS_HOVER = "#9DB2BF"  # Cor ao passar o mouse sobre célula
COLOR_WIDGET_DRAG_LABEL = "#ffeb3b"  # Cor do label de arrasto
COLOR_BTN_SUCCESS = "#5cb85c"  # Cor de botão de sucesso
COLOR_BTN_DANGER = "#d9534f"  # Cor de botão de perigo
COLOR_BTN_SAVE = "#3c8e40"  # Cor de botão de salvar
COLOR_WIDGET_LIST = "#2d2d40"  # Cor da lista de widgets

# Variável para armazenar informações de arrastar e soltar
# Estrutura: {'widget': nome, 'origem': widget_ref, 'label': label_ref}
drag_info = {'widget': None, 'origem': None, 'label': None}

# Lista para armazenar as células disponíveis na tela E-Ink
celulas = []

# Lista para armazenar as linhas da grade desenhadas
grid_lines = []

# Dicionário para armazenar informações dos widgets por célula
widget_infos = {}

# Lista de páginas, cada uma com layout e widgets
pages = [{'layout': '1x1', 'widgets': {}}]

current_page = 0  # Índice da página atual
modo_atual = '1x1'  # Layout atual

tela_global = None  # Referência global para a tela principal
page_label = None  # Label de paginação
layout_var = None  # Variável de controle do OptionMenu de layout
delete_btn = None  # Botão de deletar página
auth_btn = None  # Botão de autenticação

# --- Funções principais da interface ---
def criar_janela():
    """Cria a janela principal da aplicação."""
    janela = ctk.CTk()  # Cria a instância da janela principal do customtkinter.
    janela.title("Minha Janela")  # Define o título da janela.
    janela.geometry("800x690")  # Define as dimensões da janela (largura x altura).
    return janela  # Retorna o objeto da janela criada.


def criar_layout(janela):
    """Cria o layout da janela principal, incluindo sidebar e tela."""
    global tela_global  # Declara que usará a variável global 'tela_global'.
    main = ctk.CTkFrame(janela, fg_color="transparent")  # Cria o frame principal com fundo transparente.
    main.pack(side='right', fill='both', expand=True)  # Posiciona o frame principal à direita, preenchendo o espaço.
    sidebar = ctk.CTkFrame(janela, width=200)  # Cria a barra lateral com largura fixa.
    sidebar.pack(side='left', fill='y')  # Posiciona a barra lateral à esquerda, preenchendo na vertical.
    tela = ctk.CTkFrame(main, width=400, height=300, fg_color=COLOR_CANVAS, border_width=2)  # Cria a tela de visualização (canvas).
    tela.pack(pady=150, padx=20)  # Posiciona a tela com espaçamento (padding).
    tela.pack_propagate(False)  # Impede que a tela redimensione para caber o conteúdo.
    tela_global = tela  # Armazena a referência da tela na variável global.
    return main, sidebar, tela  # Retorna os frames criados.


def dividir_tela(modo, tela):
    """Divide a tela E-Ink em células e desenha a grade por cima."""
    global celulas, modo_atual, grid_lines  # Declara o uso de variáveis globais.
    modo_atual = modo  # Atualiza o modo de layout atual.
    # Limpa widgets antigos das células e as linhas da grade
    [w.destroy() for w in tela.winfo_children()]  # Remove todos os widgets filhos da tela.
    celulas.clear()  # Limpa a lista de células.
    grid_lines.clear()  # Limpa a lista de linhas da grade.
    # Layouts possíveis com suas coordenadas e dimensões relativas
    layouts = {
        '2x2': [(0.5*j, 0.5*i, 0.5, 0.5) for i in range(2) for j in range(2)],  # Grid 2x2
        '2x1': [(0, 0.5*i, 1, 0.5) for i in range(2)],  # Grid 2x1 (2 linhas, 1 coluna)
        '1x2': [(0.5*j, 0, 0.5, 1) for j in range(2)],  # Grid 1x2 (1 linha, 2 colunas)
        '1x1': [(0, 0, 1, 1)]  # Grid 1x1 (tela cheia)
    }
    # Cria as células invisíveis (frames) para cada parte do layout
    for x, y, w, h in layouts[modo]:
        celula = ctk.CTkFrame(tela, fg_color="transparent", border_width=0)  # Cria um frame transparente.
        celula.place(relx=x, rely=y, relwidth=w, relheight=h)  # Posiciona e dimensiona a célula.
        celulas.append(celula)  # Adiciona a célula à lista de células.
    # Desenha as linhas da grade por cima das células
    line_color = "gray30"  # Define a cor da linha da grade.
    line_thickness = 1  # Define a espessura da linha da grade.
    if modo == '2x2':
        # Linha vertical para o layout 2x2
        v_line = ctk.CTkFrame(tela, width=line_thickness, fg_color=line_color)
        v_line.place(relx=0.5, rely=0, relheight=1, anchor='n')
        grid_lines.append(v_line)
        # Linha horizontal para o layout 2x2
        h_line = ctk.CTkFrame(tela, height=line_thickness, fg_color=line_color)
        h_line.place(relx=0, rely=0.5, relwidth=1, anchor='w')
        grid_lines.append(h_line)
    elif modo == '1x2':
        # Linha vertical para o layout 1x2
        v_line = ctk.CTkFrame(tela, width=line_thickness, fg_color=line_color)
        v_line.place(relx=0.5, rely=0, relheight=1, anchor='n')
        grid_lines.append(v_line)
    elif modo == '2x1':
        # Linha horizontal para o layout 2x1
        h_line = ctk.CTkFrame(tela, height=line_thickness, fg_color=line_color)
        h_line.place(relx=0, rely=0.5, relwidth=1, anchor='w')
        grid_lines.append(h_line)


def mudar_layout_da_pagina(modo):
    """Atualiza o layout da página atual ao selecionar novo layout."""
    if pages:  # Verifica se a lista de páginas não está vazia.
        pages[current_page]['layout'] = modo  # Define o novo layout para a página atual.
    carregar_pagina()  # Recarrega a página para aplicar as mudanças.


def find_cell_under_cursor(window):
    """Encontra a célula sob o cursor do mouse subindo na hierarquia de widgets."""
    x, y = window.winfo_pointerxy()  # Obtém as coordenadas globais do cursor.
    widget_under_cursor = window.winfo_containing(x, y)  # Encontra o widget diretamente sob o cursor.
    current_widget = widget_under_cursor  # Inicia a busca a partir do widget encontrado.
    while current_widget:  # Loop para subir na hierarquia de widgets.
        if current_widget in celulas:  # Verifica se o widget atual é uma das células.
            return current_widget  # Retorna a célula encontrada.
        try:
            current_widget = current_widget.master  # Sobe para o widget pai (master).
        except AttributeError:
            return None  # Retorna None se chegar ao topo sem encontrar uma célula.
    return None  # Retorna None se o loop terminar.


def iniciar_drag(event, widget_nome, janela, widget_ref):
    """Inicia o processo de arrastar um widget da lista."""
    drag_info.update({'widget': widget_nome, 'origem': widget_ref})  # Armazena informações do widget arrastado.
    widget_ref.configure(fg_color='#444')  # Altera a cor do widget para dar um feedback visual de "pressionado".
    # Cria um label flutuante que segue o cursor
    drag_info['label'] = ctk.CTkLabel(janela, text=WIDGETS[widget_nome],
                                  fg_color=COLOR_WIDGET_DRAG_LABEL, text_color='#333',
                                  font=('Arial', 12, 'bold'),
                                  corner_radius=6, padx=8, pady=4)
    janela.config(cursor='hand2')  # Altera o cursor do mouse para indicar que algo está sendo arrastado.
    janela.bind('<Motion>', lambda e: atualizar_drag(e, janela))  # Associa o movimento do mouse à função de atualização.


def atualizar_drag(event, janela):
    """Atualiza a posição do label de arrasto e destaca célula sob o cursor."""
    if drag_info['label']:  # Verifica se o label de arrasto existe.
        x = janela.winfo_pointerx() - janela.winfo_rootx() + 10  # Calcula a posição X do label.
        y = janela.winfo_pointery() - janela.winfo_rooty() + 10  # Calcula a posição Y do label.
        drag_info['label'].place(x=x, y=y)  # Atualiza a posição do label.
        cell_under_cursor = find_cell_under_cursor(janela)  # Encontra a célula sob o cursor.
        for celula in celulas:  # Itera sobre todas as células.
            if celula.winfo_exists():  # Verifica se a célula ainda existe.
                is_over = (celula == cell_under_cursor)  # Confere se o cursor está sobre esta célula.
                celula.configure(fg_color=COLOR_CANVAS_HOVER if is_over else 'transparent')  # Destaca a célula se o cursor estiver sobre ela.


def finalizar_drag(event, janela):
    """Finaliza o processo de arrastar e soltar o widget na célula."""
    celula = find_cell_under_cursor(janela)  # Encontra a célula de destino.
    if celula and drag_info['widget']:  # Se uma célula e um widget arrastado existirem.
        [w.destroy() for w in celula.winfo_children()]  # Remove qualquer widget que já esteja na célula.
        # Cria um novo label para o widget dentro da célula
        widget_label = ctk.CTkLabel(celula, text=WIDGETS[drag_info['widget']], 
                                    fg_color="transparent", font=('Arial', 14, 'bold'))
        widget_label.pack(expand=True, fill='both')  # Posiciona o label para preencher a célula.
        widget_label.bind('<Double-Button-1>', lambda e, nome=drag_info['widget'], c=celula: mostrar_popup(nome, c))  # Adiciona evento de duplo clique.
        widget_infos[celula] = {'tipo': drag_info['widget']}  # Salva a informação do novo widget na célula.
    if drag_info['origem']:  # Se o widget de origem (da lista) existir.
        drag_info['origem'].configure(fg_color=COLOR_WIDGET_LIST)  # Restaura a cor original do widget na lista.
    if drag_info['label']:  # Se o label flutuante de arrasto existir.
        drag_info['label'].destroy()  # Remove o label flutuante.
    [c.configure(fg_color='transparent') for c in celulas if c.winfo_exists()]  # Restaura a cor de todas as células.
    janela.unbind('<Motion>')  # Remove o evento de movimento do mouse.
    janela.config(cursor='')  # Restaura o cursor padrão.
    drag_info.update({'widget': None, 'origem': None, 'label': None})  # Limpa as informações de arrasto.

# --- Funções de autenticação Google ---
def verificar_token():
    """Verifica se existe token salvo para autenticação."""
    return os.path.exists('token.json')  # Retorna True se o arquivo 'token.json' existir, False caso contrário.

def fazer_login():
    """Realiza login no Google e salva token."""
    try:
        if verificar_token():  # Verifica se o usuário já está logado.
            service = autenticar_gmail()  # Tenta autenticar com o token existente.
            if service:  # Se a autenticação for bem-sucedida.
                messagebox.showinfo("Info", "Você já está logado!")  # Informa que o login já foi feito.
                atualizar_botao_auth()  # Atualiza o botão de autenticação.
                return  # Encerra a função.
        messagebox.showinfo("Login", "O navegador será aberto para fazer login no Google.\nFeche esta mensagem e aguarde...")  # Pede para o usuário aguardar.
        service = autenticar_gmail()  # Inicia o fluxo de autenticação (abre o navegador).
        if verificar_token() and service:  # Se o token foi criado e o serviço foi obtido.
            messagebox.showinfo("Sucesso", "Login realizado com sucesso!")  # Informa o sucesso.
        else:
            messagebox.showerror("Erro", "Falha no login. Tente novamente.")  # Informa a falha.
    except Exception as e:
        messagebox.showerror("Erro", f"Erro durante o login: {e}")  # Exibe mensagem de erro genérica.
    finally:
        atualizar_botao_auth()  # Garante que o botão de autenticação seja atualizado no final.

def fazer_logout():
    """Remove o token de autenticação e faz logout."""
    try:
        if os.path.exists('token.json'):  # Verifica se o arquivo de token existe.
            os.remove('token.json')  # Remove o arquivo de token.
            messagebox.showinfo("Sucesso", "Logout realizado com sucesso!")  # Informa o sucesso.
        atualizar_botao_auth()  # Atualiza o estado do botão de autenticação.
    except Exception as e:
        messagebox.showerror("Erro", f"Erro durante o logout: {e}")  # Exibe mensagem de erro.

def atualizar_botao_auth():
    """Atualiza o texto e ação do botão de autenticação conforme estado."""
    global auth_btn  # Declara o uso da variável global do botão.
    if auth_btn:  # Verifica se o botão já foi criado.
        if verificar_token():  # Se o usuário estiver logado.
            auth_btn.configure(text='🔓 Logout Google', command=fazer_logout, fg_color=COLOR_BTN_DANGER)  # Configura para logout.
        else:  # Se não estiver logado.
            auth_btn.configure(text='🔑 Login Google', command=fazer_login, fg_color=COLOR_BTN_SUCCESS)  # Configura para login.

# --- Funções para controles da barra lateral ---
def criar_controles(sidebar, tela, janela):
    """Cria os controles e widgets na barra lateral."""
    global layout_var, page_label, auth_btn, delete_btn  # Declara o uso de variáveis globais.
    # Cria e posiciona o botão de autenticação
    auth_btn = ctk.CTkButton(sidebar, text='🔑 Login Google', command=fazer_login,
                           font=('Arial', 12, 'bold'))
    auth_btn.pack(pady=10, fill='x', padx=16)
    atualizar_botao_auth()  # Define o estado inicial do botão.
    # Cria e posiciona o label e o menu de seleção de layout
    ctk.CTkLabel(sidebar, text="Layout da grade:", font=('Arial', 10, 'bold')).pack(pady=(10,2), anchor='w', padx=10)
    layout_var = ctk.StringVar(value='1x1')  # Variável para armazenar a seleção do layout.
    opcoes_layout = ['1x1', '1x2', '2x1', '2x2']  # Lista de layouts disponíveis.
    layout_menu = ctk.CTkOptionMenu(sidebar, variable=layout_var, values=opcoes_layout,
                                     command=lambda m: mudar_layout_da_pagina(m))
    layout_menu.pack(pady=(0, 15), fill='x', padx=16)
    # Cria e posiciona o label da lista de widgets
    ctk.CTkLabel(sidebar, text="Widgets disponíveis:", font=('Arial', 10, 'bold')).pack(pady=(10,5), anchor='w', padx=10)
    # Cria um label arrastável para cada widget disponível
    for nome, label_text in WIDGETS.items():
        widget_label = ctk.CTkLabel(sidebar, text=label_text, fg_color=COLOR_WIDGET_LIST,
                                    font=('Arial', 13, 'bold'), anchor='w', padx=10,
                                    corner_radius=6, cursor='hand2')
        widget_label.pack(fill='x', padx=16, pady=4, ipady=8)
        # Associa os eventos de clique e soltar para o drag-and-drop
        widget_label.bind('<Button-1>', lambda e, n=nome, w=widget_label: iniciar_drag(e, n, janela, w))
        widget_label.bind('<ButtonRelease-1>', lambda e: finalizar_drag(e, janela))
    # Cria um frame para os botões de ação (Salvar, Deletar)
    action_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    action_frame.pack(side='bottom', pady=10)
    # Cria e posiciona o botão de salvar configuração
    save_btn = ctk.CTkButton(action_frame, text='Salvar Configuração', command=salvar_configuracao_em_json,
                            fg_color=COLOR_BTN_SAVE, font=('Arial', 12, 'bold'))
    save_btn.pack(pady=5)
    # Cria o botão de deletar página (inicialmente pode estar oculto)
    delete_btn = ctk.CTkButton(action_frame, text='Deletar Página', command=deletar_pagina_atual,
                             fg_color=COLOR_BTN_DANGER, font=('Arial', 12, 'bold'))
    # Cria um frame para os controles de navegação de página
    nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    nav_frame.pack(side='bottom', pady=10)
    # Cria e posiciona o botão de página anterior
    prev_btn = ctk.CTkButton(nav_frame, text='< Prev', command=pagina_anterior, width=80)
    prev_btn.pack(side='left', padx=5)
    # Cria e posiciona o label que mostra o número da página
    page_label = ctk.CTkLabel(nav_frame, text='', font=('Arial', 10, 'bold'))
    page_label.pack(side='left', padx=5)
    # Cria e posiciona o botão de próxima página
    next_btn = ctk.CTkButton(nav_frame, text='Next >', command=proxima_pagina, width=80)
    next_btn.pack(side='left', padx=5)
    atualizar_label_pagina()  # Define o texto inicial do label da página.

# --- Funções auxiliares para widgets ---
def get_campos_widget(widget_nome):
    """Retorna os campos de configuração para cada tipo de widget."""
    # Dicionário que mapeia tipos de widget a seus campos de configuração
    campos_dict = {
        'Notícias': [('Tema', 'tema')],
        'Clima': [('Região', 'regiao')],
        'Eventos': [('Data inicial', 'data_inicial'), ('Data final', 'data_final'), ('Título do evento', 'titulo_evento')],
        'Email': [('Remetente', 'remetente')],
        'Reddit': [('Subreddits (separados por vírgula)', 'subreddits'), ('Filtro de tempo', 'time_filter')]
    }
    print(widget_infos)
    return campos_dict.get(widget_nome, [])  # Retorna a lista de campos ou uma lista vazia.


def mostrar_popup(widget_nome, celula):
    """Exibe popup para configurar propriedades do widget."""
    popup = ctk.CTkToplevel()  # Cria uma nova janela (popup).
    popup.title(f"Widget: {WIDGETS[widget_nome]}")  # Define o título da popup.
    popup.geometry("370x380" if widget_nome == 'Reddit' else "370x280")  # Define o tamanho da popup (maior para Reddit).
    popup.transient()  # Mantém a popup na frente da janela principal.
    popup.grab_set()  # Torna a popup modal (bloqueia interação com a janela principal).
    ctk.CTkLabel(popup, text=f"{WIDGETS[widget_nome]}", font=("Arial", 14, 'bold')).pack(pady=(15,10))  # Adiciona um título.
    entradas = {}  # Dicionário para armazenar os campos de entrada.
    campos = get_campos_widget(widget_nome)  # Obtém os campos para o widget.
    
    info_salva = widget_infos.get(celula, {})  # Obtém as informações já salvas para este widget.
    
    # Cria um label e um campo de entrada para cada campo de configuração
    for label, key in campos:
        # Remove o campo 'Número de posts' do Reddit
        if widget_nome == 'Reddit' and key == 'limit':
            continue
        ctk.CTkLabel(popup, text=label+':', font=("Arial", 10)).pack(anchor='w', padx=20)
        # Tratamento especial para o time_filter do Reddit (dropdown)
        if widget_nome == 'Reddit' and key == 'time_filter':
            time_filter_var = ctk.StringVar(value=info_salva.get('time_filter', 'week'))
            time_filter_options = ['hour', 'day', 'week', 'month', 'year', 'all']
            time_filter_menu = ctk.CTkOptionMenu(popup, variable=time_filter_var, values=time_filter_options)
            time_filter_menu.pack(fill='x', padx=20, pady=2)
            entradas[key] = time_filter_var  # Armazena a variável do dropdown
        else:
            entry = ctk.CTkEntry(popup, font=("Arial", 11), border_width=2)
            entry.pack(fill='x', padx=20, pady=2)
            entradas[key] = entry  # Armazena a referência do campo de entrada.
    
    # Adiciona texto de ajuda específico para Reddit
    if widget_nome == 'Reddit':
        help_frame = ctk.CTkFrame(popup, fg_color="transparent")
        help_frame.pack(anchor='w', padx=20, pady=10)
        help_text = "💡 Dicas:\n• Subreddits: technology, programming, science\n• Número de posts: sempre 7\n• Filtro: week = última semana"
        ctk.CTkLabel(help_frame, text=help_text, font=("Arial", 9), 
                    text_color="gray", justify="left").pack(anchor='w')
    
    # Adiciona checkboxes específicos para o widget de Email
    if widget_nome == 'Email':
        lido_var = ctk.BooleanVar(value=info_salva.get('lido', False))
        importante_var = ctk.BooleanVar(value=info_salva.get('importante', False))
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(anchor='w', padx=18, pady=5)
        ctk.CTkCheckBox(frame, text="Lido", variable=lido_var).pack(side='left')
        ctk.CTkCheckBox(frame, text="Importante", variable=importante_var).pack(side='left', padx=10)
    
    # Preenche os campos de entrada com os dados já salvos
    for key, entry in entradas.items():
        if key in info_salva:
            if widget_nome == 'Reddit' and key == 'time_filter':
                # time_filter já foi definido no dropdown acima
                continue
            else:
                entry.insert(0, info_salva[key])
    
    # Valores padrão para Reddit se não houver dados salvos
    if widget_nome == 'Reddit' and not info_salva:
        if 'subreddits' in entradas:
            entradas['subreddits'].insert(0, "technology")
    
    # Função interna para salvar os dados da popup
    def salvar():
        dados = {'tipo': widget_nome}  # Inicia o dicionário de dados com o tipo do widget.
        for key, entry in entradas.items():
            if widget_nome == 'Reddit' and key == 'time_filter':
                dados[key] = entry.get()  # Para dropdown, usa .get() da StringVar
            else:
                value = entry.get()  # Obtém o valor de cada campo de entrada.
                # Processamento especial para Reddit
                if widget_nome == 'Reddit':
                    if key == 'subreddits':
                        # Converte string separada por vírgulas em lista
                        if value:
                            subreddits_list = [s.strip() for s in value.split(',') if s.strip()]
                            dados[key] = subreddits_list if subreddits_list else ['technology']
                        else:
                            dados[key] = ['technology']
                    else:
                        dados[key] = value
                else:
                    dados[key] = value
        if widget_nome == 'Reddit':
            dados['limit'] = 7  # Sempre salva 7, mesmo sem campo
        if widget_nome == 'Email':
            dados['lido'] = lido_var.get()  # Obtém o valor do checkbox 'lido'.
            dados['importante'] = importante_var.get()  # Obtém o valor do checkbox 'importante'.
        widget_infos[celula] = dados  # Atualiza as informações do widget na célula.
        popup.destroy()  # Fecha a popup.
    ctk.CTkButton(popup, text="Salvar", command=salvar, fg_color=COLOR_BTN_SAVE).pack(pady=15)  # Cria o botão de salvar.
    popup.wait_window()  # Espera a popup ser fechada antes de continuar.

# --- Funções de manipulação de páginas ---
def salvar_pagina():
    """Salva o layout e widgets da página atual na lista de páginas."""
    global pages, current_page, modo_atual  # Declara o uso de variáveis globais.
    page_widgets = {}  # Dicionário para armazenar os widgets da página.
    for celula, info in widget_infos.items():  # Itera sobre os widgets na tela.
        if celula in celulas:  # Verifica se a célula do widget ainda existe.
            idx = celulas.index(celula)  # Obtém o índice da célula.
            page_widgets[idx] = info  # Salva as informações do widget usando o índice.
    pages[current_page] = {'layout': modo_atual, 'widgets': page_widgets}  # Atualiza os dados da página atual.


def carregar_pagina():
    """Carrega o layout e widgets da página atual na interface."""
    global widget_infos, tela_global, layout_var  # Declara o uso de variáveis globais.
    if not (0 <= current_page < len(pages)): return  # Garante que o índice da página é válido.
    widget_infos.clear()  # Limpa as informações de widgets da tela.
    page_config = pages[current_page]  # Obtém a configuração da página atual.
    layout_da_pagina = page_config.get('layout', '1x1')  # Obtém o layout da página.
    widgets_da_pagina = page_config.get('widgets', {})  # Obtém os widgets da página.
    dividir_tela(layout_da_pagina, tela_global)  # Aplica o layout à tela.
    if layout_var:
        layout_var.set(layout_da_pagina)  # Atualiza o valor do menu de seleção de layout.
    # Adiciona os widgets à tela conforme a configuração carregada
    for idx, dados in widgets_da_pagina.items():
        if idx < len(celulas):  # Verifica se o índice do widget é válido.
            cel = celulas[idx]  # Obtém a célula correspondente.
            # Cria o label do widget na célula
            widget_label = ctk.CTkLabel(cel, text=WIDGETS[dados['tipo']],
                                    fg_color="transparent", font=('Arial', 14, 'bold'))
            widget_label.pack(expand=True, fill='both')
            # Associa o evento de duplo clique para abrir a popup de configuração
            widget_label.bind('<Double-Button-1>', lambda e, nome=dados['tipo'], c=cel: mostrar_popup(nome, c))
            widget_infos[cel] = dados  # Armazena as informações do widget.
    atualizar_label_pagina()  # Atualiza o indicador de página.


def proxima_pagina():
    """Avança para a próxima página, salvando o estado atual."""
    global current_page, pages, modo_atual  # Declara o uso de variáveis globais.
    salvar_pagina()  # Salva o estado da página atual antes de mudar.
    current_page += 1  # Incrementa o índice da página.
    if current_page >= len(pages):  # Se for uma nova página.
        pages.append({'layout': modo_atual, 'widgets': {}})  # Adiciona uma nova página em branco.
    carregar_pagina()  # Carrega a nova página.


def pagina_anterior():
    """Volta para a página anterior, salvando o estado atual."""
    global current_page  # Declara o uso da variável global.
    if current_page > 0:  # Verifica se não está na primeira página.
        salvar_pagina()  # Salva o estado da página atual.
        current_page -= 1  # Decrementa o índice da página.
        carregar_pagina()  # Carrega a página anterior.k


def atualizar_label_pagina():
    """Atualiza o texto do label de paginação e visibilidade do botão deletar."""
    global page_label, delete_btn  # Declara o uso de variáveis globais.
    if page_label:  # Se o label de página existir.
        page_label.configure(text=f"Página {current_page + 1}/{len(pages)}")  # Atualiza o texto.
    if delete_btn:  # Se o botão de deletar existir.
        if len(pages) > 1:  # Se houver mais de uma página.
            delete_btn.pack(pady=5)  # Mostra o botão de deletar.
        else:
            delete_btn.pack_forget()  # Esconde o botão de deletar.


def deletar_pagina_atual():
    """Deleta a página atual após confirmação do usuário."""
    global current_page, pages  # Declara o uso de variáveis globais.
    if len(pages) <= 1:  # Impede a exclusão da única página.
        messagebox.showwarning("Aviso", "Não é possível deletar a única página disponível.")
        return
    # Pede confirmação ao usuário
    resposta = messagebox.askyesno("Confirmar Deleção",
                                  f"Tem certeza de que deseja deletar a Página {current_page + 1}?\n\nEsta ação não pode ser desfeita.")
    if not resposta:  # Se o usuário cancelar.
        return
    pages.pop(current_page)  # Remove a página atual da lista.
    if current_page >= len(pages):  # Se a página deletada era a última.
        current_page = len(pages) - 1  # Vai para a nova última página.
    carregar_pagina()  # Recarrega a interface.
    messagebox.showinfo("Sucesso", "Página deletada com sucesso!")  # Informa o sucesso.

# --- Funções para salvar/carregar configuração em JSON ---
def _get_row_col_from_index(index, layout):
    """Converte índice de célula para linha e coluna conforme layout."""
    if layout == '2x2': return index // 2, index % 2  # Lógica para grid 2x2.
    if layout == '1x2': return 0, index  # Lógica para grid 1x2.
    if layout == '2x1': return index, 0  # Lógica para grid 2x1.
    if layout == '1x1': return 0, 0  # Lógica para grid 1x1.
    return 0, 0  # Padrão.


def _transformar_para_formato_json():
    """Transforma as páginas e widgets para o formato do arquivo JSON."""
    output = {"paginas": []}  # Estrutura principal do JSON.
    for i, page_data in enumerate(pages):  # Itera sobre cada página.
        layout = page_data['layout']  # Obtém o layout da página.
        widgets_internos = page_data['widgets']  # Obtém os widgets da página.
        widgets_json = []  # Lista para armazenar os widgets no formato JSON.
        for index, info in widgets_internos.items():  # Itera sobre cada widget.
            linha, coluna = _get_row_col_from_index(index, layout)  # Converte índice para linha/coluna.
            dados_widget = {k: v for k, v in info.items() if k != 'tipo'}  # Pega os dados do widget (exceto o tipo).
            # Garante que o Reddit sempre salva limit=7
            if info['tipo'].lower() == 'reddit':
                dados_widget['limit'] = 7
            # Adiciona o widget formatado à lista
            widgets_json.append({
                "tipo": info['tipo'].lower(),
                "linha": linha,
                "coluna": coluna,
                "dados": dados_widget
            })
        # Adiciona a página formatada à lista de páginas
        output["paginas"].append({
            "numeroPagina": i + 1,
            "modoPagina": layout,
            "widgets": widgets_json
        })
    return output  # Retorna o dicionário completo pronto para ser salvo como JSON.


def salvar_configuracao_em_json():
    """Salva a configuração atual em arquivo dashboard.json."""
    salvar_pagina()  # Garante que a página atual está salva na memória.
    dados_para_salvar = _transformar_para_formato_json()  # Converte os dados para o formato JSON.
    try:
        with open('dashboard.json', 'w', encoding='utf-8') as f:  # Abre o arquivo para escrita.
            json.dump(dados_para_salvar, f, indent=2, ensure_ascii=False)  # Salva os dados no arquivo.
        messagebox.showinfo("Sucesso", "Configuração salva com sucesso em dashboard.json")  # Informa o sucesso.
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o arquivo:\n{e}")  # Informa erro.


def _get_index_from_row_col(linha, coluna, layout):
    """Converte linha e coluna para índice de célula conforme layout."""
    if layout == '2x2': return linha * 2 + coluna  # Lógica para grid 2x2.
    elif layout == '1x2': return coluna  # Lógica para grid 1x2.
    elif layout == '2x1': return linha  # Lógica para grid 2x1.
    elif layout == '1x1': return 0  # Lógica para grid 1x1.
    return 0  # Padrão.


def carregar_configuracao_do_json():
    """Carrega configuração do dashboard.json para as páginas."""
    global pages, current_page  # Declara o uso de variáveis globais.
    if not os.path.exists('dashboard.json'):  # Verifica se o arquivo de configuração existe.
        return
    try:
        with open('dashboard.json', 'r', encoding='utf-8') as f:  # Abre o arquivo para leitura.
            dados = json.load(f)  # Carrega os dados do JSON.
        pages.clear()  # Limpa as páginas existentes.
        current_page = 0  # Reseta para a primeira página.
        for pagina_data in dados.get('paginas', []):  # Itera sobre cada página no arquivo.
            layout = pagina_data.get('modoPagina', '1x1')  # Obtém o layout.
            widgets_json = pagina_data.get('widgets', [])  # Obtém a lista de widgets.
            widgets_internos = {}  # Dicionário para os widgets no formato interno.
            for widget_data in widgets_json:  # Itera sobre cada widget.
                linha = widget_data.get('linha', 0)
                coluna = widget_data.get('coluna', 0)
                index = _get_index_from_row_col(linha, coluna, layout)  # Converte linha/coluna para índice.
                info_widget = {'tipo': widget_data['tipo'].capitalize()}  # Formata o tipo do widget.
                info_widget.update(widget_data.get('dados', {}))  # Adiciona os dados do widget.
                widgets_internos[index] = info_widget  # Armazena o widget.
            pages.append({'layout': layout, 'widgets': widgets_internos})  # Adiciona a página carregada.
        if not pages:  # Se o arquivo estava vazio.
            pages = [{'layout': '1x1', 'widgets': {}}]  # Cria uma página padrão.
    except Exception as e:
        messagebox.showerror("Erro ao Carregar", f"Erro ao carregar dashboard.json:\n{e}")  # Informa erro.
        pages = [{'layout': '1x1', 'widgets': {}}]  # Cria uma página padrão em caso de erro.

# --- Função principal (main) ---
def main():
    """Função principal que inicializa a aplicação e interface."""
    ctk.set_appearance_mode("Dark")  # Define o tema da aplicação como escuro.
    ctk.set_default_color_theme("blue")  # Define a cor padrão dos widgets.
    carregar_configuracao_do_json()  # Carrega a configuração salva, se existir.
    janela = criar_janela()  # Cria a janela principal.
    main_area, sidebar, tela = criar_layout(janela)  # Cria os frames principais.
    criar_controles(sidebar, tela, janela)  # Adiciona os controles na barra lateral.
    janela.after(100, carregar_pagina)  # Agenda o carregamento da primeira página após a inicialização.
    janela.mainloop()  # Inicia o loop principal da aplicação.

# --- Execução do programa ---
if __name__ == "__main__":
    main()  # Chama a função principal quando o script é executado diretamente.
