import json
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from get_embeddings_function import get_embedding_function
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score


# Caminho do banco de dados e JSON analítico
CHROMA_PATH = "C:/Users/pedro/OneDrive/Documentos/basesdedefeitos/chroma_db"
JSON_ANALITICO_PATH = "contexto_analitico.json"
INTERACOES_PATH = "interacoes.json"  # Arquivo para salvar as interações

# Ground truth atualizado
ground_truth = {
    "Quais os bugs relacionados a CTO? Quais áreas do sistema podem estar impactadas?": {"keywords": ["CTO"], "relevant_keys": ["CTO"]},
    "O banco de defeitos contém registros de falhas envolvendo splitter? Quais setores do sistema são afetados?": {"keywords": ["splitter"], "relevant_keys": ["splitter"]},
    "O banco jirabugs.csv possui relatos de falhas ligadas à OLT? Existe alguma área do sistema mais suscetível a esses problemas?": {"keywords": ["OLT"], "relevant_keys": ["OLT"]},
    "Houve registros de defeitos envolvendo cabos no banco de defeitos? Como podemos apontar possíveis áreas críticas do sistema a partir disso?": {"keywords": ["cabo"], "relevant_keys": ["cabo"]},
    "Existe algum padrão nos defeitos relacionados a splitter, CTO e CEO no banco jirabugs.csv? Como essas falhas se relacionam entre si dentro do sistema?": {"keywords": ["CTO", "CEO", "Splitter"], "relevant_keys": ["CTO", "CEO", "Splitter"]},
    "Foram identificados problemas no sistema relacionados a MAC?": {"keywords": ["MAC"], "relevant_keys": ["MAC"]},
    "O termo 'Uplink' aparece em relatórios de falhas no banco jirabugs.csv?": {"keywords": ["Uplink"], "relevant_keys": ["Uplink"]},
    "Há registros de bugs relacionados a 'mapa' no banco jirabugs.csv?": {"keywords": ["mapa"], "relevant_keys": ["mapa"]},
    "Os registros no banco jirabugs.csv indicam problemas com o botão 'Salvar'? Em quais contextos esse problema ocorre?": {"keywords": ["Salvar"], "relevant_keys": ["Salvar"]},
    "'Erro desconhecido' foi registrado no sistema? Em quais situações essa mensagem aparece?": {"keywords": ["Erro desconhecido"], "relevant_keys": ["Erro desconhecido"]},
    "Quais os reports de Epic Link BR-27": {"keywords": ["BR-27"], "relevant_keys": ["BR-27"]},
    "O que foi reportado na Key BR-2015?": {"keywords": ["Splitter", "CTO"], "relevant_keys": ["splitter", "CTO"]},
    "Pesquise os reports feitos na Sprint 32 e faça um relatório sobre esses reports": {"keywords": ["Sprint 32"], "relevant_keys": ["Sprint 32"]},
    "Quais relatos foram feitos pelo reporter Ismayle Santos? Quais tipos de problemas ele reportou?": {"keywords": ["Ismayle"], "relevant_keys": ["Ismayle"]},
    "Analise os problemas associados a linked issues BR-1154. Esses defeitos possuem um padrão?": {"keywords": ["BR-1154"], "relevant_keys": ["BR-1154"]},
    "Qual a cor do cavalo branco de napoleão?": {"keywords": ["cavalo branco"], "relevant_keys": ["cavalo branco"]},
    "Com quantos paus se faz uma canoa?": {"keywords": ["canoa"], "relevant_keys": ["canoa"]},
    "Quanto é 10+10?": {"keywords": ["10"], "relevant_keys": ["10"]},
    "Qual o esporte mais praticado no mundo?": {"keywords": ["esporte"], "relevant_keys": ["esporte"]},
    "Indique um catálogo de filmes lançados em 2024": {"keywords": ["filmes"], "relevant_keys": ["filmes"]},

    # English translations
    "What are the bugs related to CTO? Which areas of the system might be impacted?": {"keywords": ["CTO"], "relevant_keys": ["CTO"]},
    "Does the defect database contain records of failures involving splitters? Which sectors of the system are affected?": {"keywords": ["splitter"], "relevant_keys": ["splitter"]},
    "Does the jirabugs.csv database contain reports of failures related to OLT? Is there any area of the system more susceptible to these issues?": {"keywords": ["OLT"], "relevant_keys": ["OLT"]},
    "Were there records of defects involving cables in the defect database? How can we identify potential critical areas of the system from this?": {"keywords": ["cabo"], "relevant_keys": ["cabo"]},
    "Is there any pattern in the defects related to splitters, CTO, and CEO in the jirabugs.csv database? How do these failures relate to each other within the system?": {"keywords": ["CTO", "CEO", "Splitter"], "relevant_keys": ["CTO", "CEO", "Splitter"]},
    "Were any issues related to MAC identified in the system?": {"keywords": ["MAC"], "relevant_keys": ["MAC"]},
    "Does the term 'Uplink' appear in failure reports in the jirabugs.csv database?": {"keywords": ["Uplink"], "relevant_keys": ["Uplink"]},
    "Are there records of bugs related to 'map' in the jirabugs.csv database?": {"keywords": ["map"], "relevant_keys": ["map"]},
    "Do the records in the jirabugs.csv database indicate issues with the 'Save' button? In what contexts does this problem occur?": {"keywords": ["Salva"], "relevant_keys": ["Salva"]},
    "Was 'Unknown error' recorded in the system? In what situations does this message appear?": {"keywords": ["Erro Desconhecido"], "relevant_keys": ["Erro Desconhecido"]},
    "What are the reports for Epic Link BR-27?": {"keywords": ["BR-27"], "relevant_keys": ["BR-27"]},
    "What was reported in Key BR-2015?": {"keywords": ["Splitter", "CTO"], "relevant_keys": ["splitter", "CTO"]},
    "Search for reports made in Sprint 32 and create a report on these issues.": {"keywords": ["Sprint 32"], "relevant_keys": ["Sprint 32"]},
    "What reports were made by the reporter Ismayle Santos? What types of issues did he report?": {"keywords": ["Ismayle"], "relevant_keys": ["Ismayle"]},
    "Analyze the issues associated with linked issues BR-1154. Do these defects have a pattern?": {"keywords": ["BR-1154"], "relevant_keys": ["BR-1154"]},
    "What is the color of Napoleon's white horse?": {"keywords": ["white horse"], "relevant_keys": ["white horse"]},
    "How many sticks does it take to make a canoe?": {"keywords": ["canoe"], "relevant_keys": ["canoe"]},
    "What is 10+10?": {"keywords": ["10"], "relevant_keys": ["10"]},
    "What is the most practiced sport in the world?": {"keywords": ["sport"], "relevant_keys": ["sport"]},
    "Provide a catalog of movies released in 2024.": {"keywords": ["movies"], "relevant_keys": ["movies"]}
}

LIMIAR_RELEVANCIA = 0.50  # 50% dos documentos devem conter a palavra-chave para ser considerado relevante

def convert_to_binary(retrieved_docs, relevant_keys):
    """
    Converte retrieved_docs e relevant_keys em listas binárias.
    
    - retrieved_docs: Lista de documentos recuperados.
    - relevant_keys: Lista de palavras-chave relevantes.

    Retorna:
    - y_true: Lista binária indicando se cada documento recuperado é relevante (1 = relevante, 0 = não relevante).
    - y_pred: Lista binária indicando se cada documento foi recuperado (1 = recuperado, 0 = não recuperado).
    """
    relevant_keys = [key.lower() for key in relevant_keys]  # Normaliza as palavras-chave

    y_true = [1 if any(key in doc.lower() for key in relevant_keys) else 0 for doc in retrieved_docs]
    y_pred = [1] * len(retrieved_docs)  # Todos os documentos recuperados são considerados 1

    return y_true, y_pred

def precision_at_k(y_true, y_pred, k):
    """
    Calcula a precisão no topo k dos documentos recuperados.

    Retorna:
    - Precisão no topo k.
    """
    k = max(1, k)  # Evita divisão por zero
    return precision_score(y_true[:k], y_pred[:k], zero_division=0)

def recall_at_k(y_true, y_pred, k):
    """
    Calcula o recall no topo k dos documentos recuperados.

    Retorna:
    - Recall no topo k.
    """
    k = max(1, k)
    return recall_score(y_true[:k], y_pred[:k], zero_division=0)

def f1_score_at_k(y_true, y_pred, k):
    """
    Calcula o F1-score no topo k dos documentos recuperados usando sklearn.metrics.f1_score.

    Retorna:
    - F1-score no topo k.
    """
    k = max(1, k)
    return f1_score(y_true[:k], y_pred[:k], zero_division=0)

def average_precision(y_true, y_pred):
    """
    Calcula a precisão média (Average Precision, AP) usando sklearn.metrics.average_precision_score.

    Retorna:
    - Precisão média (AP).
    """
    return average_precision_score(y_true, y_pred)


def calculate_relevance(retrieved_docs, keyword):
    """Calcula a relevância verificando quantos documentos contêm a palavra-chave."""
    relevant_count = sum(1 for doc in retrieved_docs if keyword.lower() in doc.lower())
    relevance_ratio = relevant_count / len(retrieved_docs) if retrieved_docs else 0
    return relevance_ratio

def salvar_interacao(query, documentos, resposta, metricas):
    """Salva a interação em um arquivo JSON."""
    try:
        with open(INTERACOES_PATH, 'r', encoding='utf-8') as f:
            interacoes = json.load(f)
    except FileNotFoundError:
        interacoes = []
    
    interacoes.append({
        "query": query,
        "documentos": documentos,
        "resposta": resposta,
        "metricas": metricas
    })
    
    with open(INTERACOES_PATH, 'w', encoding='utf-8') as f:
        json.dump(interacoes, f, ensure_ascii=False, indent=4)

def filter_relevant_docs(retrieved_docs, keywords):
    """Filtra os documentos recuperados que contêm pelo menos uma das palavras-chave."""
    return [doc for doc in retrieved_docs if any(keyword.lower() in doc.lower() for keyword in keywords)]

        
def calcular_metricas(retrieved_docs, keywords, relevant_keys, k=2):
    """Calcula todas as métricas de avaliação."""
    relevant_docs = filter_relevant_docs(retrieved_docs, keywords)
    total_non_relevant = len(retrieved_docs) - len(relevant_docs)

    # Converter para listas binárias
    y_true, y_pred = convert_to_binary(retrieved_docs, relevant_keys)

    return {
        "precision_at_k": precision_at_k(y_true, y_pred, k),
        "recall_at_k": recall_at_k(y_true, y_pred, k),
        "f1_score": f1_score_at_k(y_true, y_pred, k),
        "average_precision": average_precision(y_true, y_pred),
    }        
        

def query_data():
    """Executa a consulta para uma pergunta específica."""
    PROMPT_TEMPLATE = """
    You are an assistant specialized in answering questions about defects in a GPON (Gigabit Passive Optical Network) management system. Your task is to analyze the provided context and generate accurate, concise, and relevant responses in Portuguese.

    ### Context:
    You are working with a Jira defect report database (jirabugs.csv) related to a web-based GPON network management system. 

    ### Data Structure:
    The defect reports are organized in a CSV file with the following columns:
    1. **Issue Type**: The type of issue (e.g., "Dev Bug", "Bug", "Task"). This indicates the nature of the defect.
    2. **Key**: A unique identifier for the defect (e.g., "BR-3054"). Use this to reference specific defects.
    3. **Summary**: A brief description of the defect. This provides details about the issue.
    4. **Status**: The current status of the defect (e.g., "To Do", "In Progress", "Done"). This indicates the progress in resolving the issue.
    5. **Created**: The date and time when the defect was reported.
    6. **Linked Issues**: A list of related defect keys (e.g., "BR-2335, BR-2946"). These indicate dependencies or related issues.
    7. **Development**: Additional development-related information (usually empty or contains metadata).
    8. **Epic Link**: The key of the Epic to which the defect belongs (e.g., "BR-897"). Epics group related defects.
    9. **Reporter**: The name of the person who reported the defect.
    10. **Epic Name**: The name of the Epic (usually empty in the data).
    11. **Sprint**: The Sprint in which the defect is being addressed (e.g., "BR Sprint 37"). Sprints are time-boxed development cycles.

    ### Instructions:
    1. **Understand the Query**: Carefully analyze the query to identify the GPON network components, system functionalities or system areas being questioned.
    2. **Use the Context**: The defect reports may provide insights into recurring failures and critical areas.
    3. **Retrieved Documents**: Below the context, you will find a list of retrieved documents (defect reports) that are relevant to the query. Use these documents to provide specific details in your response.
    4. **Critical analysis and Inference**: Try to identify hidden patterns based on retrieved defects.
       - Example: If multiple bugs mention CTO and connection failures, this may indicate a structural issue in CTO management.
       - Relate defects to potential system-critical areas (e.g., ONU provisioning interface, OLT integration, splitter registration stability).
    5. **Response Format**: Your response should be in Portuguese and follow this format:
       - Start with "Resposta:" followed by a direct and specific answer to the query.
       - Include relevant details from the retrieved documents, such as summaries, and affected areas.
       - If possible, infer systemic problems or recurring trends.
       - Conclude by listing the sources (defect keys) used in the response.

    ### Example:
    Query: "Quais os bugs relacionados a CTO no banco de defeitos jirabugs.csv? Qual a possível área do sistema afetada?"
    Resposta: Os bugs relacionados a CTO incluem problemas de conexão com cabos de distribuição, instanciação incorreta e exibição de mensagens de erro. A área do sistema afetada é a funcionalidade de gerenciamento de CTOs, especificamente a interface de conexão e instanciação. 
    Fontes: BR-2199, BR-2200, BR-1773.

    ### Data for Analysis:
    - Context: {contexto}
    - Query: {pergunta_do_usuário}
    """


    query_text = input("❓ Sua pergunta: ")
    
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    print("🔍 Consultando o banco de dados Chroma para contexto adicional...")
    results = db.similarity_search_with_score(query_text, k=20)

    retrieved_docs = [doc.page_content for doc, _ in results]  # Documentos recuperados

    print("📊 Carregando contexto analítico do JSON...")
    with open(JSON_ANALITICO_PATH, 'r', encoding='utf-8') as arquivo_json:
        contexto_analitico = json.load(arquivo_json)

    contexto_analitico_texto = (
        f"Contagem total de bugs: {contexto_analitico['contagem_total_bugs']}\n\n"
        f"Contagem de bugs por Epic Link:\n{contexto_analitico['contagem_epic_link']}\n\n"
        f"Contagem de bugs por release:\n{contexto_analitico['contagem_bugs_release']}"
    )

    combined_context = f"{contexto_analitico_texto}\n\n---\n\n" + "\n\n---\n\n".join(retrieved_docs)
    print(f"📄 Contexto combinado:\n{combined_context}")

    prompt = PROMPT_TEMPLATE.format(contexto=combined_context, pergunta_do_usuário=query_text)

    print("🤖 Consultando a LLM com o prompt gerado...")
    model = OllamaLLM(model="mistral")
    response = model.invoke(prompt).strip()
    
    sources = [doc.metadata.get("id", "Desconhecido") for doc, _ in results]
    formatted_response = f"💡 Resposta: {response}\n🔗 Fontes: {sources}"

    # Calcular métricas
    if query_text in ground_truth:
        keywords = ground_truth[query_text]["keywords"]
        relevant_keys = ground_truth[query_text]["relevant_keys"]
        relevant_docs = filter_relevant_docs(retrieved_docs, keywords)  # Filtra documentos relevantes
        total_non_relevant = len(retrieved_docs) - len(relevant_docs)
        k = 4  # Definir o K para avaliação

        # Converter para listas binárias
        y_true, y_pred = convert_to_binary(retrieved_docs, relevant_keys)

        metricas = {
            "precision_at_k": precision_at_k(y_true, y_pred, k),
            "recall_at_k": recall_at_k(y_true, y_pred, k),
            "f1_score": f1_score_at_k(y_true, y_pred, k),
            "average_precision": average_precision(y_true, y_pred),
        }

        # Salvar interação com métricas
        salvar_interacao(query_text, retrieved_docs, response, metricas)
            
    print(formatted_response)
    return formatted_response

if __name__ == "__main__":
    query_data()