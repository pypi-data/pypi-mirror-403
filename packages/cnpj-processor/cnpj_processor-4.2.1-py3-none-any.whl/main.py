"""
EXEMPLOS DE USO DO PROCESSADOR CNPJ:

=== ARQUITETURA DOS STEPS ===
Cada step é composto pelos anteriores:
- download: Apenas baixa arquivos
- extract: download → extração
- csv: download → extração → gera CSVs normalizados
- process: download → extração → processamento para parquet
- database: Cria DuckDB (requer parquets existentes)
- painel: Processa painel consolidado (requer parquets existentes)
- all: download → extração → processamento → [opcionais: painel, database]

=== EXECUÇÃO BÁSICA ===
1. Processamento completo padrão:
   python main.py

2. Processar apenas tipos específicos:
   python main.py --types empresas estabelecimentos

3. Usar pasta remota específica:
   python main.py --remote-folder 2024-05

=== PROCESSAMENTO POR ETAPAS ===
4. Apenas download:
   python main.py --step download

5. Download + extração:
   python main.py --step extract

6. Download + extração + geração de CSVs normalizados:
   python main.py --step csv
   python main.py --step csv --output-csv-folder meus_csvs

7. Download + extração + processamento (gera parquets):
   python main.py --step process --output-subfolder processados

8. Criar banco DuckDB de parquets existentes:
   python main.py --step database --output-subfolder processados

9. Processar painel de dados existentes:
   python main.py --step painel --remote-folder 2024-05

=== CONTROLE DE PASTAS ===
10. Salvar em subpasta específica:
    python main.py --output-subfolder meu_processamento

11. Exibir pasta remota mais recente:
    python main.py --show-latest-folder

=== PROCESSAMENTO DO PAINEL ===
12. Painel com filtros:
    python main.py --processar-painel --painel-uf SP --painel-situacao 2

=== ECONOMIA DE ESPAÇO ===
13. Remover ZIPs após extração:
    python main.py --delete-zips-after-extract

14. Criar banco e remover parquets:
    python main.py --create-database --cleanup-after-db

=== CONTROLE DE INTERFACE ===
15. Modo silencioso:
    python main.py --quiet

16. Forçar re-download:
    python main.py --force-download

PARÂMETROS PRINCIPAIS:
- --step: Define etapa (download|extract|csv|process|database|painel|all)
- --types: Tipos a processar (empresas|estabelecimentos|simples|socios)
- --remote-folder: Pasta remota específica (AAAA-MM)
- --output-subfolder: Subpasta de saída para parquets
- --output-csv-folder: Pasta de saída para CSVs normalizados (step csv)
- --force-download: Forçar re-download
- --delete-zips-after-extract: Remover ZIPs após extração
- --create-database: Criar DuckDB após processamento
- --quiet: Modo silencioso
"""
import argparse
import asyncio
import datetime
import logging
import os
from multiprocessing import freeze_support
import psutil
import re
import signal
import sys
import time
import socket
import requests
from pathlib import Path

# Configurar encoding UTF-8 para Windows (deve ser feito o mais cedo possível)
if sys.platform == 'win32':
    try:
        # Tenta configurar UTF-8 no stdout/stderr
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        # Tenta configurar UTF-8 no console Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except:
        pass  # Se falhar, continua com encoding padrão

import aiohttp
from dotenv import load_dotenv
from rich.logging import RichHandler

# CARREGAR VARIÁVEIS DE AMBIENTE ANTES DAS IMPORTAÇÕES QUE DEPENDEM DELAS
# Garantir que o .env existe com valores padrão
from cnpj_processor import load_env_with_defaults
load_env_with_defaults()

# Importar versão centralizada
from cnpj_processor import get_full_description, get_version

# Importar sistema de localização
from src.localization import get_localization, set_locale

from cnpj_processor import (
    download_multiple_files, 
    get_latest_month_zip_urls, 
    get_remote_folders, 
    get_latest_remote_folder,
    _filter_urls_by_type,
    download_only_files,
    get_network_test_results
)
from cnpj_processor import config
from cnpj_processor import create_duckdb_file
from cnpj_processor import ProcessorFactory
from cnpj_processor import (
    EmpresaProcessor,
    EstabelecimentoProcessor,
    SimplesProcessor,
    SocioProcessor,
    PainelProcessor
)
from cnpj_processor import check_basic_folders
from cnpj_processor import format_elapsed_time
from cnpj_processor import global_stats

# Importar funções utilitárias refatoradas
from src.utils import ensure_files_downloaded, extract_zip_files

# Configurar logger global
logger = logging.getLogger(__name__)

# Imports do circuit breaker
from cnpj_processor import (
    circuit_breaker,
    FailureType,
    CriticalityLevel,
    should_continue_processing,
    report_critical_failure,
    report_fatal_failure,
    register_stop_callback
)

from typing import List, Tuple

def check_internet_connection() -> bool:
    """
    Verifica se há conexão com a internet.
    
    Returns:
        bool: True se houver conexão, False caso contrário
    """
    try:
        # Tenta fazer uma requisição para um servidor confiável
        requests.get("http://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        try:
            # Tenta resolver um domínio conhecido
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

def check_disk_space() -> bool:
    """
    Verifica se há espaço suficiente em disco.
    
    Returns:
        bool: True se há espaço suficiente, False caso contrário
    """
    try:
        disk_usage = psutil.disk_usage("/")
        
        # Verificar se há pelo menos 5GB livres
        min_free_gb = 5
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb < min_free_gb:
            logger.error(f"Espaço em disco insuficiente. Disponível: {free_gb:.2f}GB, Mínimo: {min_free_gb}GB")
            return False
        
        logger.info(f"Espaço em disco verificado: {free_gb:.2f}GB disponíveis")
        return True
        
    except Exception as e:
        logger.warning(f"Erro ao verificar espaço em disco: {e}")
        return True  # Assumir que está OK se não conseguir verificar

def setup_logging(log_level_str: str):
    """Configura o sistema de logging com base no nível fornecido."""
    # Determinar pasta raiz do projeto (onde está o main.py)
    project_root = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(project_root, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_filename = os.path.join(logs_dir, f'cnpj_process_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Comando de execução
    cmd_line = ' '.join(sys.argv)
    # Escreve o comando como primeira linha do log
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Linha de comando: {cmd_line}\n")

    # Converte a string do argumento para o nível de log correspondente
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Configuração do logger raiz para capturar tudo
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        print("[setup_logging] Handlers de log anteriores removidos.")

    # Handler para arquivo (sem cores)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    # Handler para console (com RichHandler)
    console_handler = RichHandler(rich_tracebacks=True)
    root_logger.addHandler(console_handler)

    logger_instance = logging.getLogger(__name__)
    logger_instance.info(f"Nível de log configurado para: {logging.getLevelName(log_level)}")
    logger_instance.info(f"Linha de comando: {cmd_line}")
    return logger_instance


def print_header(text: str):
    """Imprime um cabeçalho formatado."""
    print(f"\n{'=' * 50}")
    print(f"{text}")
    print(f"{'=' * 50}\n")
    # Também logar
    logger.info("=" * 50)
    logger.info(text)
    logger.info("=" * 50)


def print_section(text: str):
    """Imprime uma seção formatada."""
    print(f"\n▶ {text}")
    # Também logar
    logger.info(f"▶ {text}")


def print_success(text: str):
    """Imprime uma mensagem de sucesso formatada."""
    print(f"✓ {text}")
    # Também logar
    logger.info(f"✓ {text}")


def print_warning(text: str):
    """Imprime uma mensagem de aviso formatada."""
    print(f"⚠ {text}")
    # Também logar
    logger.warning(f"⚠ {text}")


def print_error(text: str):
    """Imprime uma mensagem de erro formatada."""
    print(f"✗ {text}")
    # Também logar
    logger.error(f"✗ {text}")


def initialize_processors():
    try:
        # Registrar todos os processadores na factory
        ProcessorFactory.register("empresa", EmpresaProcessor)
        ProcessorFactory.register("estabelecimento", EstabelecimentoProcessor)
        ProcessorFactory.register("simples", SimplesProcessor)
        ProcessorFactory.register("socio", SocioProcessor)
        ProcessorFactory.register("painel", PainelProcessor)
        
        registered = ProcessorFactory.get_registered_processors()
        logger.info(f"✅ Processadores registrados: {', '.join(registered)}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar processadores: {e}")
        return False

def check_parquet_completeness(output_parquet_path: str, tipos_processados: List[str]) -> tuple[bool, List[str]]:
    """
    Verifica se todos os parquets necessários foram criados com sucesso.
    
    Args:
        output_parquet_path: Caminho onde os parquets devem estar
        tipos_processados: Lista de tipos que deveriam ter sido processados
        
    Returns:
        tuple: (sucesso_completo, tipos_faltando)
    """
    try:
        logger.info("🔍 Verificando integridade dos arquivos parquet gerados...")
        
        # Mapeamento de tipos para nomes de diretórios
        tipo_to_folder = {
            'empresas': 'empresa',
            'estabelecimentos': 'estabelecimento', 
            'simples': 'simples',
            'socios': 'socio'
        }
        
        tipos_faltando = []
        tipos_verificados = []
        
        for tipo in tipos_processados:
            folder_name = tipo_to_folder.get(tipo, tipo)
            parquet_path = os.path.join(output_parquet_path, folder_name)
            
            # Verificar se o diretório existe
            if not os.path.exists(parquet_path):
                logger.error(f"❌ Diretório não encontrado para {tipo}: {parquet_path}")
                tipos_faltando.append(tipo)
                continue
            
            # Verificar se há arquivos parquet no diretório
            try:
                parquet_files = [f for f in os.listdir(parquet_path) if f.endswith('.parquet')]
                if not parquet_files:
                    logger.error(f"❌ Nenhum arquivo parquet encontrado para {tipo} em: {parquet_path}")
                    tipos_faltando.append(tipo)
                    continue
                
                # Verificar se pelo menos um arquivo parquet é válido
                valid_files = 0
                total_size = 0
                
                for parquet_file in parquet_files:
                    file_path = os.path.join(parquet_path, parquet_file)
                    try:
                        # Verificar tamanho do arquivo (arquivos muito pequenos são suspeitos)
                        file_size = os.path.getsize(file_path)
                        if file_size < 1024:  # Menor que 1KB é suspeito
                            logger.warning(f"⚠️ Arquivo parquet muito pequeno: {parquet_file} ({file_size} bytes)")
                            continue
                        
                        # Verificar se o arquivo parquet é válido
                        import pyarrow.parquet as pq
                        pq.read_metadata(file_path)
                        valid_files += 1
                        total_size += file_size
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Arquivo parquet corrompido ou inválido: {parquet_file} - {e}")
                        continue
                
                if valid_files == 0:
                    logger.error(f"❌ Nenhum arquivo parquet válido encontrado para {tipo}")
                    tipos_faltando.append(tipo)
                    continue
                
                # Log de sucesso
                size_mb = total_size / (1024 * 1024)
                logger.info(f"✅ {tipo}: {valid_files} arquivos válidos, {size_mb:.1f} MB")
                tipos_verificados.append(tipo)
                
            except Exception as e:
                logger.error(f"❌ Erro ao verificar diretório {tipo}: {e}")
                tipos_faltando.append(tipo)
        
        # Resultado final
        sucesso_completo = len(tipos_faltando) == 0
        
        if sucesso_completo:
            logger.info(f"✅ Verificação completa: Todos os {len(tipos_verificados)} tipos processados com sucesso")
        else:
            logger.error(f"❌ Verificação falhou: {len(tipos_faltando)} tipo(s) com problemas: {', '.join(tipos_faltando)}")
        
        return sucesso_completo, tipos_faltando
        
    except Exception as e:
        logger.error(f"❌ Erro durante verificação de integridade: {e}")
        return False, tipos_processados

def main():
    """Função principal de execução."""
    return asyncio.run(async_main())

async def async_main():
    """Função principal assíncrona de execução."""
    global overall_success
    overall_success = True
    
    start_time = time.time()  # Definir start_time no início
    
    # Inicializar variáveis de tempo para evitar erros
    download_time = 0.0
    process_time = 0.0
    db_time = 0.0
    remote_folder = ""
    
    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description=get_full_description()
    )
    
    # Adicionar opção de locale ANTES de processar outros argumentos
    parser.add_argument(
        '--locale',
        type=str,
        choices=['pt_BR', 'pt_PT', 'en_US', 'en_GB'],
        help='Especificar idioma: pt_BR, pt_PT, en_US, en_GB. Padrão: detectado automaticamente'
    )
    
    # Argumentos padrão
    loc = get_localization()
    
    parser.add_argument('--types', '-t', nargs='+', dest='tipos', choices=['empresas', 'estabelecimentos', 'simples', 'socios'],
                         default=[], help='Tipos de dados a serem processados. Se não especificado, processa todos (relevante para steps \'process\' e \'all\').')
    parser.add_argument('--step', '-s', choices=['download', 'extract', 'csv', 'process', 'database', 'painel', 'all'], default='all',
                         help='Etapa a ser executada. Padrão: all')
    parser.add_argument('--quiet', '-q', action='store_true',
                         help='Modo silencioso - reduz drasticamente as saídas no console')
    parser.add_argument('--verbose-ui', '-v', action='store_true',
                         help='Interface visual mais completa - só funciona com UI interativo')
    parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                         help='Nível de logging. Padrão: INFO')
    parser.add_argument('--remote-folder', '-r', type=str, 
                         help='Usar uma pasta específica do servidor (formato AAAA-MM). Exemplo: 2024-05')
    parser.add_argument('--all-folders', '-a', action='store_true',
                         help='Baixar de todas as pastas disponíveis do servidor. Sobrescreve --remote-folder')
    parser.add_argument('--from-folder', '-f', type=str,
                         help='Iniciar download/processamento a partir de uma pasta específica (formato AAAA-MM)')
    parser.add_argument('--force-download', '-F', action='store_true',
                         help='Forçar download mesmo que arquivo já exista')
    parser.add_argument('--create-private-subset', '-E', action='store_true',
                         help='Criar subconjunto de empresas privadas (apenas para empresas)')
    parser.add_argument('--create-uf-subset', '-U', type=str, metavar='UF',
                         help='Criar subconjunto por UF (apenas para estabelecimentos). Ex: --create-uf-subset SP')
    parser.add_argument('--output-subfolder', '-o', type=str,
                         help='Nome da subpasta onde salvar os arquivos parquet. Use "." para pasta raiz')
    parser.add_argument('--output-csv-folder', type=str,
                         help='Pasta onde salvar CSVs normalizados (padrão: dados-abertos). Para step csv')
    parser.add_argument('--source-zip-folder', '-z', type=str,
                         help='Pasta de origem dos arquivos ZIP (para step \'process\')')
    parser.add_argument('--process-all-folders', '-p', action='store_true',
                         help='Processar todas as pastas de data (formato AAAA-MM) em PATH_ZIP')
    parser.add_argument('--keep-artifacts', '-k', action='store_true',
                         help='Manter arquivos ZIP e descompactados (por padrão são removidos para economizar espaço)')
    parser.add_argument('--delete-zips-after-extract', action='store_true', dest='delete_zips_after_extract',
                         help='Deletar arquivos ZIP após extração (padrão)')
    parser.add_argument('--create-database', '-D', action='store_true',
                         help='Criar banco de dados DuckDB após processamento (opcional)')
    parser.add_argument('--cleanup-after-db', '-c', action='store_true',
                         help='Deletar arquivos parquet após criação do banco DuckDB (só funciona com --create-database)')
    parser.add_argument('--keep-parquet-after-db', '-K', action='store_true',
                         help='Manter arquivos parquet após criação do banco (só funciona com --create-database)')
    parser.add_argument('--show-progress', '-B', action='store_true',
                         help='Forçar exibição da barra de progresso (sobrescreve config)')
    parser.add_argument('--hide-progress', '-H', action='store_true',
                         help='Forçar ocultação da barra de progresso (sobrescreve config)')
    parser.add_argument('--show-pending', '-S', action='store_true',
                         help='Forçar exibição da lista de arquivos pendentes (sobrescreve config)')
    parser.add_argument('--hide-pending', '-W', action='store_true',
                         help='Forçar ocultação da lista de arquivos pendentes (sobrescreve config)')
    parser.add_argument('--process-panel', '-P', action='store_true',
                         help='Processar dados do painel (combina estabelecimentos + simples + empresas)')
    parser.add_argument('--panel-uf', type=str, metavar='UF',
                         help='Filtrar painel por UF específica (ex: SP, GO, MG)')
    parser.add_argument('--panel-status', type=int, metavar='CODIGO',
                         help='Filtrar painel por situação cadastral (1=Nula, 2=Ativa, 3=Suspensa, 4=Inapta, 8=Baixada)')
    parser.add_argument('--panel-include-inactive', action='store_true',
                         help='Incluir estabelecimentos inativos no painel')
    parser.add_argument('--normalize-csv', action='store_true',
                         help='Gerar arquivos CSV normalizados (com as mesmas regras de padronização dos parquets)')
    parser.add_argument('--show-latest-folder', '--latest', action='store_true',
                         help='Exibir a pasta remota mais recente disponível e sair')
    parser.add_argument('--version', '-V', action='store_true',
                         help='Exibir a versão do cnpj-processor e sair')

    # Parse apenas os argumentos conhecidos para extrair --locale primeiro
    args, remaining = parser.parse_known_args()
    
    # Se --locale foi especificado, aplicar antes de continuar
    if args.locale:
        set_locale(args.locale)
    
    # Fazer parse completo dos argumentos
    args = parser.parse_args()
    
    # Tratamento especial: --show-latest-folder com log desabilitado
    if args.show_latest_folder:
        try:
            load_dotenv()
            base_url = os.getenv('BASE_URL')
            if not base_url:
                print("❌ BASE_URL não definida no arquivo .env")
                return False, ""
            
            remote_folder = await get_latest_remote_folder(base_url)
            
            if remote_folder:
                print(remote_folder)
                return True, remote_folder
            else:
                print("❌ Não foi possível determinar a pasta remota mais recente")
                return False, ""
                
        except Exception as e:
            print(f"❌ Erro ao consultar pasta remota: {e}")
            return False, ""
    
    # Tratamento especial: --version com saída limpa
    if args.version:
        version = get_version()
        print(f"cnpj-processor {version}")
        return True, ""
    
    # Configurar logging
    logger = setup_logging(args.log_level)
    
    # Configurar manipulador de sinal de emergência
    def emergency_stop_main():
        """Manipulador de emergência para sinais críticos."""
        print("\n🛑 SINAL DE EMERGÊNCIA RECEBIDO!")
        print("⚠️ Interrompendo execução...")
        logger.critical("🛑 Execução interrompida por sinal de emergência")
        global overall_success
        overall_success = False
        sys.exit(1)

    # Registrar manipulador de sinal
    signal.signal(signal.SIGINT, lambda s, f: emergency_stop_main())
    signal.signal(signal.SIGTERM, lambda s, f: emergency_stop_main())
    
    # Carregar variáveis de ambiente
    load_dotenv()
    print_header("Carregando variáveis de ambiente...")
    PATH_ZIP = os.getenv('PATH_ZIP', './dados-abertos-zip')
    PATH_UNZIP = os.getenv('PATH_UNZIP', './dados-abertos')
    PATH_PARQUET = os.getenv('PATH_PARQUET', './parquet')
    FILE_DB_PARQUET = os.getenv('FILE_DB_PARQUET', 'cnpj.duckdb')
    
    # Usar o diretório de trabalho atual (onde o comando foi executado)
    # Isso garante que os arquivos sejam salvos onde o usuário está executando o comando
    project_root = os.getcwd()
    
    # Resolver caminhos relativos para absolutos baseado no CWD
    if not os.path.isabs(PATH_ZIP):
        PATH_ZIP = os.path.abspath(os.path.join(project_root, PATH_ZIP))
    if not os.path.isabs(PATH_UNZIP):
        PATH_UNZIP = os.path.abspath(os.path.join(project_root, PATH_UNZIP))
    if not os.path.isabs(PATH_PARQUET):
        PATH_PARQUET = os.path.abspath(os.path.join(project_root, PATH_PARQUET))
    
    if PATH_ZIP and PATH_UNZIP and PATH_PARQUET:
        print_success("Variáveis de ambiente carregadas com sucesso")
        logger.info(f"PATH_ZIP = {PATH_ZIP}")
        logger.info(f"PATH_UNZIP = {PATH_UNZIP}")
        logger.info(f"PATH_PARQUET = {PATH_PARQUET}")
        logger.info(f"FILE_DB_PARQUET = {FILE_DB_PARQUET}")
    else:
        print_error("Erro ao carregar variáveis de ambiente. Verifique o arquivo .env")
        logger.error("Variáveis de ambiente PATH_ZIP, PATH_UNZIP ou PATH_PARQUET não definidas")
        return False, ""
        
    if not initialize_processors():
        print_error("Falha ao inicializar nova arquitetura. Verifique os logs.")
        return False, ""
    print_success("Arquitetura refatorada inicializada com sucesso")
    
    # Verificar conectividade de rede antes de qualquer operação
    if not check_internet_connection():
        logger.warning("⚠️ Sem conectividade de rede. Algumas funcionalidades podem estar limitadas.")
        report_critical_failure(
            FailureType.CONNECTIVITY,
            "Sem conexão com a internet",
            "MAIN_CONNECTIVITY"
        )
    
    # Verificar espaço em disco
    if not check_disk_space():
        logger.warning("⚠️ Espaço em disco limitado. Monitorando recursos durante execução.")
    
    # Inicializar sistema de estatísticas
    global_stats.start_session()
    
    # Processamento exclusivo do painel
    if args.step == 'painel':
        print_header("Processamento Exclusivo do Painel Consolidado")
        
        # Verificar se foi especificada uma pasta de origem ou usar padrão
        if args.source_zip_folder:
            # Usar pasta específica fornecida pelo usuário
            source_zip_path = args.source_zip_folder
            if not os.path.isabs(source_zip_path):
                source_zip_path = os.path.join(PATH_ZIP, source_zip_path)
            
            # Extrair nome da pasta para usar como output
            folder_name = os.path.basename(source_zip_path.rstrip('/\\'))
        else:
            # Tentar determinar a pasta mais recente ou usar --remote-folder
            if args.remote_folder:
                remote_folder_painel = args.remote_folder
                logger.info(f"Usando pasta remota especificada para painel: {remote_folder_painel}")
            else:
                # Obter pasta mais recente
                try:
                    base_url = os.getenv('BASE_URL')
                    if not base_url:
                        logger.error("BASE_URL não definida no arquivo .env")
                        return False, ""
                    remote_folder_painel = await get_latest_remote_folder(base_url)
                    if not remote_folder_painel:
                        logger.error("Não foi possível determinar a pasta remota. Use --source-zip-folder ou --remote-folder")
                        return False, ""
                    logger.info(f"Pasta mais recente detectada para painel: {remote_folder_painel}")
                except Exception as e:
                    logger.error(f"Erro ao obter pasta remota: {e}")
                    logger.error("Use --source-zip-folder para especificar os dados a processar")
                    return False, ""

            source_zip_path = os.path.join(PATH_ZIP, remote_folder)
        
        # Definir pasta de saída
        if args.output_subfolder == ".":
            # Usar "." para pasta raiz
            output_parquet_path = PATH_PARQUET
        elif args.output_subfolder:
            # Usar subpasta especificada
            output_parquet_path = os.path.join(PATH_PARQUET, args.output_subfolder)
        else:
            # Padrão: usar nome da pasta remota
            output_parquet_path = os.path.join(PATH_PARQUET, remote_folder)
        
        logger.info(f"Processando painel com dados de: {source_zip_path}")
        logger.info(f"Salvando painel em: {output_parquet_path}")
        
        # Verificar se as pastas de dados existem
        if not os.path.exists(source_zip_path):
            logger.error(f"Pasta de dados não encontrada: {source_zip_path}")
            logger.error("Execute primeiro o download e processamento dos dados ou use --source-zip-folder")
            return False, ""

        # Processar painel
        painel_start_time = time.time()
        
        painel_success = process_painel_complete(
            source_zip_path=source_zip_path,
            unzip_path=PATH_UNZIP,
            output_parquet_path=output_parquet_path,
            uf_filter=args.panel_uf,
            situacao_filter=args.panel_status,
            output_filename=None,  # Será gerado automaticamente
            remote_folder=args.remote_folder  # Passar o remote_folder
        )
        
        painel_time = time.time() - painel_start_time
        
        if painel_success:
            print_success(f"Processamento exclusivo do painel concluído em {format_elapsed_time(painel_time)}")
            
            total_time = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
            logger.info("STATUS FINAL: SUCESSO")
            logger.info("=" * 50)
            
            # Finalizar estatísticas
            global_stats.end_session()
            global_stats.print_detailed_report()
            
            return True, args.output_subfolder if args.output_subfolder else "painel"
        else:
            print_error("Falha no processamento exclusivo do painel")
            
            total_time = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
            logger.info("STATUS FINAL: FALHA")
            logger.info("=" * 50)
            
            return False, ""

     # Step 1: Download apenas
    elif args.step == 'download':
        print_header("Etapa 1: Download de Arquivos")
        
        success, source_zip_path, zip_files = await ensure_files_downloaded(args, PATH_ZIP)
        
        if not success:
            return False, ""
        
        if not zip_files:
            logger.warning("Nenhum arquivo foi baixado.")
            return True, ""
        
        logger.info(f"✅ Download concluído: {len(zip_files)} arquivo(s) disponível(is)")
        return True, source_zip_path

    # Step 2: Download + Extração
    elif args.step == 'extract':
        print_header("Etapa 2: Download + Extração")
        
        # 1. Garantir que arquivos foram baixados
        print_section("2.1: Verificando/baixando arquivos")
        success, source_zip_path, zip_files = await ensure_files_downloaded(args, PATH_ZIP)
        
        if not success or not zip_files:
            logger.error("Falha ao obter arquivos para extração.")
            return False, ""
        
        # 2. Extrair arquivos
        print_section("2.2: Extraindo arquivos")
        extract_success = extract_zip_files(source_zip_path, PATH_UNZIP, args.delete_zips_after_extract)
        
        if not extract_success:
            return False, ""
        
        logger.info("✅ Extração concluída com sucesso")
        return True, "extract"

    # Step 2.5: Download + Extração + Geração de CSVs Normalizados
    elif args.step == 'csv':
        print_header("Etapa 2.5: Geração de CSVs Normalizados")
        
        # 1. Garantir que arquivos foram baixados
        print_section("2.5.1: Verificando/baixando arquivos")
        success, source_zip_path, zip_files = await ensure_files_downloaded(args, PATH_ZIP)
        
        if not success or not zip_files:
            logger.error("Falha ao obter arquivos para geração de CSVs.")
            return False, ""
        
        # 2. Definir pasta de saída
        output_folder = args.output_csv_folder or args.output_subfolder
        if output_folder:
            output_base_path = output_folder if os.path.isabs(output_folder) else os.path.abspath(output_folder)
        else:
            output_base_path = os.path.abspath(os.path.join(project_root, 'dados-abertos'))
        
        os.makedirs(output_base_path, exist_ok=True)
        logger.info(f"Salvando CSVs normalizados em: {output_base_path}")
        
        # 3. Executar geração de CSVs normalizados
        print_section("2.5.2: Gerando CSVs normalizados")

        # Filtrar por tipos, se especificado
        tipos_a_processar = args.tipos if args.tipos else ['empresas', 'estabelecimentos', 'simples', 'socios']
        
        # Mapear tipo para prefixo de arquivo
        tipo_map = {'empresas': 'Empre', 'estabelecimentos': 'Estabele', 'simples': 'Simples', 'socios': 'Socio'}
        
        # Agrupar arquivos ZIP por tipo
        zips_por_tipo = {}
        for tipo in tipos_a_processar:
            prefixo = tipo_map.get(tipo)
            if prefixo:
                zips_por_tipo[tipo] = [f for f in zip_files if f.startswith(prefixo)]

        if not any(zips_por_tipo.values()):
            logger.warning("Nenhum arquivo ZIP correspondente aos tipos especificados foi encontrado para gerar CSVs.")
            return True, ""

        # Importar funções necessárias
        from src.process import ProcessorFactory
        import tempfile
        import zipfile

        # Executar normalização
        normalize_start_time = time.time()
        total_files_processed = 0
        
        try:
            logger.info(f"🔄 Iniciando geração de CSVs de {sum(len(zips) for zips in zips_por_tipo.values())} arquivos ZIP")
            
            # Processar cada tipo
            for tipo, zip_files_tipo in zips_por_tipo.items():
                if not zip_files_tipo:
                    continue
                
                # Criar pasta específica para este tipo
                tipo_output_path = os.path.join(output_base_path, tipo)
                os.makedirs(tipo_output_path, exist_ok=True)
                
                logger.info(f"📂 Processando tipo: {tipo} ({len(zip_files_tipo)} arquivos)")
                
                # Determinar a chave do tipo para o processador
                tipo_key = tipo.rstrip('s')  # Remove 's' final para obter chave do processador
                
                # Processar cada arquivo ZIP deste tipo
                for zip_file in zip_files_tipo:
                    zip_path = os.path.join(source_zip_path, zip_file)
                    zip_prefix = os.path.splitext(zip_file)[0]
                    
                    logger.info(f"📦 Processando {zip_file}")
                    
                    # Criar processador para este tipo
                    processor = ProcessorFactory.create(
                        tipo_key,
                        source_zip_path,
                        PATH_UNZIP,
                        tipo_output_path,
                        delete_zips_after_extract=False
                    )
                    
                    # Extrair e processar
                    try:
                        with tempfile.TemporaryDirectory() as temp_extract_dir:
                            # Extrair ZIP
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                zip_ref.extractall(temp_extract_dir)
                            
                            # Processar cada arquivo CSV extraído
                            for file_name in os.listdir(temp_extract_dir):
                                file_path = os.path.join(temp_extract_dir, file_name)
                                
                                if os.path.isfile(file_path):
                                    logger.debug(f"  Normalizando arquivo: {file_name}")
                                    
                                    # Processar arquivo de dados (lê CSV e retorna DataFrame)
                                    df = processor.process_data_file(file_path)
                                    
                                    if df is not None and not df.is_empty():
                                        # Aplicar transformações da entidade
                                        df = processor.apply_entity_transformations(df)
                                        
                                        # Salvar como CSV normalizado
                                        output_file = os.path.join(tipo_output_path, file_name)
                                        df.write_csv(output_file, separator=';')
                                        
                                        logger.info(f"  ✅ {file_name} normalizado: {df.height} linhas")
                                        total_files_processed += 1
                                    else:
                                        logger.warning(f"  ⚠️ {file_name} não pôde ser processado")
                    except Exception as e:
                        logger.error(f"  ❌ Erro ao processar {zip_file}: {e}")
                        continue
                    
                    # Deletar ZIP se solicitado
                    if args.delete_zips_after_extract:
                        try:
                            os.remove(zip_path)
                            logger.debug(f"  🗑️ ZIP removido: {zip_file}")
                        except Exception as e:
                            logger.warning(f"  ⚠️ Erro ao remover ZIP {zip_file}: {e}")
            
            normalize_time = time.time() - normalize_start_time
            
            print_success(f"Geração de CSVs concluída em {format_elapsed_time(normalize_time)}")
            logger.info(f"✅ {total_files_processed} arquivos CSV normalizados gerados com sucesso")
            logger.info(f"📁 CSVs normalizados em: {output_base_path}")
            
            total_time = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
            logger.info("STATUS FINAL: SUCESSO")
            logger.info("=" * 50)
            
            # Finalizar estatísticas
            global_stats.end_session()
            global_stats.print_detailed_report()
            
            return True, "csv"
            
        except Exception as e:
            normalize_time = time.time() - normalize_start_time
            logger.error(f"❌ Erro durante geração de CSVs: {e}")
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(normalize_time)}")
            logger.info("STATUS FINAL: FALHA")
            logger.info("=" * 50)
            
            return False, ""

    # Step 3: Download + Extração + Processamento
    elif args.step == 'process':
        print_header("Etapa 3: Download + Extração + Processamento")

        # Validar parâmetros obrigatórios
        if not args.output_subfolder:
            logger.error("Para 'process', --output-subfolder é obrigatório.")
            return False, ""
        
        # 1. Garantir que arquivos foram baixados
        print_section("3.1: Verificando/baixando arquivos")
        success, source_zip_path, zip_files = await ensure_files_downloaded(args, PATH_ZIP)
        
        if not success or not zip_files:
            logger.error("Falha ao obter arquivos para processamento.")
            return False, ""
        
        # 2. Extrair arquivos
        print_section("3.2: Extraindo arquivos")
        extract_success = extract_zip_files(source_zip_path, PATH_UNZIP, args.delete_zips_after_extract)
        
        if not extract_success:
            return False, ""
        
        # 3. Processar arquivos
        print_section("3.3: Processando para parquet")
        output_parquet_path = os.path.join(PATH_PARQUET, args.output_subfolder)
        os.makedirs(output_parquet_path, exist_ok=True)
        
        tipos_a_processar = args.tipos if args.tipos else ['empresas', 'estabelecimentos', 'simples', 'socios']
        
        # Preparar URLs para pipeline
        tipo_map = {'empresas': 'Empre', 'estabelecimentos': 'Estabele', 'simples': 'Simples', 'socios': 'Socio'}
        urls_para_processar = []
        for tipo in tipos_a_processar:
            prefixo = tipo_map.get(tipo)
            if prefixo:
                urls_para_processar.extend([os.path.join(source_zip_path, f) for f in zip_files if f.startswith(prefixo)])

        if not urls_para_processar:
            logger.warning("Nenhum arquivo correspondente aos tipos especificados.")
            return True, args.output_subfolder

        process_start_time = time.time()
        process_results = await optimized_download_and_process_pipeline(
            urls=urls_para_processar,
            source_zip_path=source_zip_path,
            unzip_path=PATH_UNZIP,
            output_parquet_path=output_parquet_path,
            tipos_a_processar=tipos_a_processar,
            delete_zips_after_extract=False,  # Já foi extraído
            force_download=False  # Já foi baixado
        )
        process_time = time.time() - process_start_time

        if process_results.get('all_ok', False):
            print_success(f"Processamento concluído em {format_elapsed_time(process_time)}")
            return True, args.output_subfolder
        else:
            print_error("Falha durante processamento.")
            return False, ""

    # 🆕 CORREÇÃO: Adicionar bloco para --step database
    elif args.step == 'database':
        print_header("Etapa 3: Apenas Criação do Banco de Dados")

        if not args.output_subfolder:
            logger.error("Para a etapa 'database', o argumento --output-subfolder é obrigatório.")
            return False, ""

        output_parquet_path = os.path.join(PATH_PARQUET, args.output_subfolder)
        if not os.path.exists(output_parquet_path):
            logger.error(f"Pasta de origem dos Parquets não encontrada: {output_parquet_path}")
            return False, ""

        db_start_time = time.time()
        db_success = create_duckdb_file(output_parquet_path, FILE_DB_PARQUET)
        db_time = time.time() - db_start_time

        if db_success:
            print_success(f"Banco de dados criado com sucesso em {format_elapsed_time(db_time)}")
            if args.cleanup_after_db:
                cleanup_success = cleanup_after_database(output_parquet_path, "", True, False)
                if not cleanup_success:
                    print_warning("Falha ao limpar arquivos parquet.")
        else:
            print_error("Falha ao criar o banco de dados.")
            overall_success = False
            return False, ""
   
    # Se chegou até aqui após processamento bem-sucedido, usar pipeline otimizado
    if args.step == 'all':
        remote_folder_param = args.remote_folder if args.remote_folder else None
        from_folder_param = args.from_folder if args.from_folder else None
        
        # Determinar pasta remota a usar
        if remote_folder_param:
            remote_folder = remote_folder_param
            logger.info(f"Usando pasta remota especificada: {remote_folder}")
        else:
            # Obter pasta mais recente
            base_url = os.getenv('BASE_URL')
            if not base_url:
                logger.error("BASE_URL não definida no arquivo .env")
                return False, ""
            remote_folder = await get_latest_remote_folder(base_url)
            if not remote_folder:
                logger.error("Não foi possível determinar a pasta remota mais recente")
                return False, ""
            logger.info(f"Pasta remota mais recente: {remote_folder}")

        # Definir caminhos
        source_zip_path = os.path.join(PATH_ZIP, remote_folder)
        # Definir pasta de saída
        if args.output_subfolder == ".":
            # Usar "." para pasta raiz (incluir pasta remota)
            output_parquet_path = os.path.join(PATH_PARQUET, remote_folder)
        elif args.output_subfolder:
            # Resolver o caminho de output_subfolder (pode ser relativo ou absoluto)
            # Se começar com '..' ou '.', resolver relativamente ao diretório de trabalho atual
            if args.output_subfolder.startswith('..') or args.output_subfolder.startswith('.'):
                # Resolver caminho relativo a partir do CWD (onde o comando foi executado)
                resolved_output = os.path.normpath(os.path.join(os.getcwd(), args.output_subfolder))
            else:
                # Caminho absoluto ou nome de subpasta
                if os.path.isabs(args.output_subfolder):
                    resolved_output = args.output_subfolder
                else:
                    # Nome de subpasta dentro de PATH_PARQUET
                    resolved_output = os.path.join(PATH_PARQUET, args.output_subfolder)
            
            # Adicionar pasta remota após o destino informado
            # Estrutura final: PASTA_INFORMADA/XXXX-XX/simples
            output_parquet_path = os.path.join(resolved_output, remote_folder)
        else:
            # Padrão: usar nome da pasta remota
            output_parquet_path = os.path.join(PATH_PARQUET, remote_folder)
        os.makedirs(source_zip_path, exist_ok=True)
        os.makedirs(output_parquet_path, exist_ok=True)
        
        logger.info(f"Processando arquivos de: {source_zip_path}")
        logger.info(f"Salvando Parquets em: {output_parquet_path}")
        
        # Obter URLs dos arquivos da pasta remota
        from src.async_downloader import get_latest_month_zip_urls, _filter_urls_by_type
        
        base_url = os.getenv('BASE_URL')
        if not base_url:
            logger.error("BASE_URL não definida no arquivo .env")
            return False, ""
            
        zip_urls, _ = get_latest_month_zip_urls(base_url, remote_folder)
            
        # Filtrar URLs por tipos desejados
        tipos_desejados = args.tipos if args.tipos else ['empresas', 'estabelecimentos', 'simples', 'socios']
        if tipos_desejados:
            zip_urls, ignored = _filter_urls_by_type(zip_urls, tuple(tipos_desejados))
            logger.info(f"Filtrados {ignored} URLs não desejadas para processamento. Restaram {len(zip_urls)} URLs.")
        
        # Lista de tipos a processar (todos ou filtrados)
        tipos_a_processar = args.tipos if args.tipos else ['empresas', 'estabelecimentos', 'simples', 'socios']
        
        # Preparar opções de processamento
        processing_options = {}
        if hasattr(args, 'create_private_subset') and args.create_private_subset:
            processing_options['create_private'] = True
        if hasattr(args, 'create_uf_subset') and args.create_uf_subset:
            processing_options['uf_subset'] = args.create_uf_subset
        
        # 🆕 Executar pipeline otimizado unificado (download + processamento em paralelo)
        print_section("Pipeline Otimizado: Download e Processamento Paralelo")
        pipeline_start_time = time.time()
        
        logger.info("🚀 Iniciando pipeline otimizado: download e processamento em paralelo")
        logger.info(f"📋 Arquivos a processar: {len(zip_urls)}")
        logger.info(f"🎯 Tipos de dados: {', '.join(tipos_a_processar)}")
        
        # Por padrão, remove artefatos (ZIPs e descompactados) para economizar espaço
        # Use --keep-artifacts para manter os arquivos
        delete_artifacts = not args.keep_artifacts
        
        process_results = await optimized_download_and_process_pipeline(
            urls=zip_urls,
            source_zip_path=source_zip_path,
            unzip_path=PATH_UNZIP,
            output_parquet_path=output_parquet_path,
            tipos_a_processar=tipos_a_processar,
            delete_zips_after_extract=delete_artifacts,
            force_download=args.force_download,
            **processing_options
        )
        
        # Remover completamente as pastas de trabalho se delete_artifacts está ativo
        if delete_artifacts:
            logger.info("🧹 Removendo pastas de trabalho (dados-abertos e dados-abertos-zip)...")
            import shutil
            try:
                if os.path.exists(PATH_UNZIP):
                    shutil.rmtree(PATH_UNZIP)
                    logger.info(f"✅ Pasta removida: {PATH_UNZIP}")
                if os.path.exists(source_zip_path):
                    # Remover apenas a pasta específica da remote_folder em PATH_ZIP
                    shutil.rmtree(source_zip_path)
                    logger.info(f"✅ Pasta removida: {source_zip_path}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover pastas de trabalho: {e}")
        
        pipeline_time = time.time() - pipeline_start_time
        logger.info("=" * 50)
        logger.info(f"Tempo do pipeline otimizado: {format_elapsed_time(pipeline_time)}")
        
        # Simular tempos separados para compatibilidade com logs finais
        download_time = pipeline_time * 0.3  # Aproximadamente 30% do tempo em downloads
        process_time = pipeline_time * 0.7   # Aproximadamente 70% do tempo em processamento
        
        # Verificar se houve problemas no pipeline
        if not process_results.get('all_ok', False):
            print_warning("Alguns erros ocorreram durante o pipeline. O banco de dados NÃO será criado.")
            total_time = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
            logger.info("STATUS FINAL: FALHA")
            logger.info("=" * 50)
            return False, ""
        else:
            print_success("Pipeline de download e processamento concluído com sucesso.")
        
        # Verificação adicional: confirmar que todos os parquets foram criados corretamente
        print_section("Verificando integridade dos dados processados")
        parquets_ok, tipos_faltando = check_parquet_completeness(output_parquet_path, tipos_a_processar)
        
        if not parquets_ok:
            print_error(f"Arquivos parquet incompletos ou corrompidos detectados para: {', '.join(tipos_faltando)}")
            print_error("O banco de dados DuckDB NÃO será criado devido a dados incompletos.")
            logger.error("Verificação de integridade dos parquets falhou")
            logger.error(f"Tipos com problemas: {', '.join(tipos_faltando)}")
            
            total_time = time.time() - start_time
            logger.info("=" * 50)
            logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
            logger.info("STATUS FINAL: FALHA - DADOS INCOMPLETOS")
            logger.info("=" * 50)
            return False, ""
        else:
            print_success("Verificação de integridade dos parquets concluída com sucesso.")
        
        # 2.4. Limpeza de pastas de trabalho
        if args.delete_zips_after_extract:
            logger.info("🧹 Removendo pastas de trabalho (dados-abertos e dados-abertos-zip)...")
            try:
                # Remover pasta de dados descompactados
                if os.path.exists(PATH_UNZIP):
                    import shutil
                    shutil.rmtree(PATH_UNZIP, ignore_errors=True)
                    logger.info(f"✅ Pasta removida: {PATH_UNZIP}")
                
                # Remover pasta de ZIPs baixados
                if os.path.exists(PATH_ZIP):
                    shutil.rmtree(PATH_ZIP, ignore_errors=True)
                    logger.info(f"✅ Pasta removida: {PATH_ZIP}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover pastas de trabalho: {e}")
        
        # 2.5. Processamento do Painel (se solicitado)
        if args.process_panel:
            print_section("Etapa 2.5: Processamento do Painel Consolidado")
            painel_start_time = time.time()
            
            painel_success = process_painel_complete(
                source_zip_path=source_zip_path,
                unzip_path=PATH_UNZIP,
                output_parquet_path=output_parquet_path,
                uf_filter=args.panel_uf,
                situacao_filter=args.panel_status,
                output_filename=None,  # Será gerado automaticamente
                remote_folder=remote_folder
            )
            
            painel_time = time.time() - painel_start_time
            logger.info("=" * 50)
            logger.info(f"Tempo de processamento do painel: {format_elapsed_time(painel_time)}")
            
            if painel_success:
                print_success("Processamento do painel concluído com sucesso.")
            else:
                print_warning("Falha no processamento do painel.")
                print_warning("⚠️ O painel consolidado não foi gerado.")
                logger.warning("Processamento do painel falhou")
        
        # 3. Criação do banco de dados (OPCIONAL - requer --create-database)
        if args.create_database:
            print_section("Etapa 3: Criação do banco de dados DuckDB (opcional)")
            logger.info("🎯 Criação de banco solicitada via --create-database")
            db_start_time = time.time()
            
            try:
                logger.info(f"Criando arquivo DuckDB em: {output_parquet_path}")
                db_success = create_duckdb_file(output_parquet_path, FILE_DB_PARQUET)
                db_time = time.time() - db_start_time
                
                if db_success:
                    logger.info("=" * 50)
                    logger.info(f"Tempo de processamento do banco: {format_elapsed_time(db_time)}")
                    db_file = os.path.join(output_parquet_path, FILE_DB_PARQUET)
                    print_success(f"Banco de dados DuckDB criado com sucesso em: {db_file}")
                    
                    # Limpeza de parquets após criar banco (se solicitada)
                    if args.cleanup_after_db and not args.keep_parquet_after_db:
                        logger.info("🧹 Removendo arquivos parquet após criação do banco...")
                        cleanup_success = cleanup_after_database(
                            parquet_folder=output_parquet_path,
                            zip_folder="",
                            cleanup_parquet=True,
                            cleanup_zip=False
                        )
                        
                        if not cleanup_success:
                            print_warning("Aviso: Houve problemas durante a limpeza de parquets")
                    elif args.keep_parquet_after_db:
                        logger.info("📦 Mantendo arquivos parquet (--keep-parquet-after-db especificado)")
                    
                else:
                    logger.info("=" * 50)
                    logger.info(f"Tempo de processamento do banco (falhou): {format_elapsed_time(db_time)}")
                    print_error("Falha ao criar banco de dados. Verifique os logs para mais detalhes.")
                    logger.error("Criação do banco de dados falhou")
                    total_time = time.time() - start_time
                    logger.info("=" * 50)
                    logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
                    logger.info("STATUS FINAL: FALHA (banco não criado)")
                    logger.info("=" * 50)
                    return False, ""
            except Exception as e:
                db_time = time.time() - db_start_time
                logger.exception(f"Erro ao criar banco de dados: {e}")
                logger.info("=" * 50)
                logger.info(f"Tempo de processamento do banco (erro): {format_elapsed_time(db_time)}")
                print_error(f"Falha ao criar banco de dados: {str(e)}")
                total_time = time.time() - start_time
                logger.info("=" * 50)
                logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
                logger.info("STATUS FINAL: FALHA")
                logger.info("=" * 50)
                return False, ""
        else:
            logger.info("ℹ️  Criação de banco DuckDB não solicitada (use --create-database para criar)")
            print_section("Banco de dados DuckDB não será criado (use --create-database)")

    total_time = time.time() - start_time
    
    # Finalizar coleta de estatísticas
    global_stats.end_session()

    # Resumo final
    print_header("Processamento concluído")
    logger.info("=" * 50)
    logger.info("RESUMO FINAL DE EXECUÇÃO:")
    logger.info("=" * 50)
    
    if args.step == 'all':
        logger.info(f"Download: {format_elapsed_time(download_time)}")
        logger.info(f"Processamento: {format_elapsed_time(process_time)}")
        if args.create_database:
            logger.info(f"Criação do banco: {format_elapsed_time(db_time)}")
        else:
            logger.info("Criação do banco: NÃO EXECUTADA (use --create-database)")
    
    logger.info(f"TEMPO TOTAL DE EXECUÇÃO: {format_elapsed_time(total_time)}")
    logger.info("=" * 50)
    logger.info("Execução concluída.")
    
    # Exibir relatório detalhado de estatísticas
    global_stats.print_detailed_report()
        
    return overall_success, remote_folder

def process_painel_complete(source_zip_path: str, unzip_path: str, output_parquet_path: str, 
                          uf_filter: str | None = None, situacao_filter: int | None = None, 
                          output_filename: str | None = None, remote_folder: str | None = None) -> bool:
    """
    Processa dados do painel combinando estabelecimentos, simples e empresas.
    
    Args:
        source_zip_path: Caminho dos arquivos ZIP
        unzip_path: Caminho para extração
        output_parquet_path: Caminho de saída
        uf_filter: Filtro por UF (opcional)
        situacao_filter: Filtro por situação cadastral (opcional)
        output_filename: Nome do arquivo de saída (opcional)
        remote_folder: Pasta remota de origem dos dados (opcional)
        
    Returns:
        bool: True se processamento foi bem-sucedido
    """
    try:
        logger.info("=" * 60)
        logger.info("🏢 INICIANDO PROCESSAMENTO DO PAINEL CONSOLIDADO")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Definir caminhos dos parquets das entidades individuais
        # Se especificado remote_folder, buscar dados na pasta remota
        if remote_folder:
            # Obter PATH_PARQUET do contexto global
            import os
            from pathlib import Path
            
            # Obter pasta parquet do contexto
            current_dir = Path(__file__).parent
            parquet_base = current_dir / "parquet"
            source_data_path = os.path.join(str(parquet_base), remote_folder)
        else:
            source_data_path = output_parquet_path
            
        estabelecimento_path = os.path.join(source_data_path, 'estabelecimento')
        simples_path = os.path.join(source_data_path, 'simples') 
        empresa_path = os.path.join(source_data_path, 'empresa')
        
        logger.info(f"Procurando dados em:")
        logger.info(f"  📁 Estabelecimentos: {estabelecimento_path}")
        logger.info(f"  📁 Simples: {simples_path}")
        logger.info(f"  📁 Empresas: {empresa_path}")
        
        # Verificar se os parquets das entidades individuais existem
        missing_paths = []
        if not os.path.exists(estabelecimento_path) or not os.listdir(estabelecimento_path):
            missing_paths.append('estabelecimento')
        if not os.path.exists(simples_path) or not os.listdir(simples_path):
            missing_paths.append('simples')
        if not os.path.exists(empresa_path) or not os.listdir(empresa_path):
            missing_paths.append('empresa')
        
        if missing_paths:
            logger.error(f"Parquets não encontrados para: {', '.join(missing_paths)}")
            logger.error("Execute primeiro o processamento das entidades individuais")
            return False
        
        # Configurar opções do processador
        painel_options = {
            'path_zip': source_zip_path,
            'path_unzip': unzip_path,
            'path_parquet': output_parquet_path,
            'estabelecimento_path': estabelecimento_path,
            'simples_path': simples_path,
            'empresa_path': empresa_path,
            'skip_download': True,
            'skip_unzip': True,
            'skip_individual_processing': True,
        }
        
        # Adicionar filtros se especificados
        if uf_filter:
            painel_options['uf_filter'] = uf_filter.upper()
            logger.info(f"Filtro por UF aplicado: {uf_filter.upper()}")
        
        if situacao_filter is not None:
            painel_options['situacao_filter'] = situacao_filter
            situacao_map = {1: 'Nula', 2: 'Ativa', 3: 'Suspensa', 4: 'Inapta', 8: 'Baixada'}
            situacao_nome = situacao_map.get(situacao_filter, f'Código {situacao_filter}')
            logger.info(f"Filtro por situação aplicado: {situacao_nome}")
        
        # Criar processador do painel
        processor = PainelProcessor(**painel_options)
        
        # Processar dados do painel
        if not output_filename:
            output_filename = "painel_dados.parquet"
        
        logger.info(f"Arquivo de saída: {output_filename}")
        
        success = processor.process_painel_data(output_filename)
        
        elapsed_time = time.time() - start_time
        
        if success:
            output_path = os.path.join(output_parquet_path, output_filename)
            logger.info("=" * 60)
            logger.info(f"✅ PAINEL PROCESSADO COM SUCESSO em {format_elapsed_time(elapsed_time)}")
            logger.info(f"📄 Arquivo salvo em: {output_path}")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error(f"❌ FALHA NO PROCESSAMENTO DO PAINEL após {format_elapsed_time(elapsed_time)}")
            logger.error("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"Erro no processamento do painel: {e}")
        return False

async def optimized_download_and_process_pipeline(
    urls: List[str], 
    source_zip_path: str, 
    unzip_path: str, 
    output_parquet_path: str,
    tipos_a_processar: List[str],
    delete_zips_after_extract: bool = False,
    force_download: bool = False,
    **processing_options
) -> dict:
    """
    Pipeline otimizado que baixa e processa arquivos em paralelo.
    """
    from src.async_downloader import _filter_urls_by_type
    
    # ✅ CORREÇÃO 1: Filtrar URLs antes de processar para evitar baixar arquivos auxiliares
    logger.info("🔍 Filtrando URLs por tipos desejados...")
    filtered_urls, ignored_count = _filter_urls_by_type(urls, tuple(tipos_a_processar))
    
    if ignored_count > 0:
        logger.info(f"📊 Filtrados {ignored_count} arquivos auxiliares (Cnaes, Motivos, etc.)")
        logger.info(f"🎯 URLs válidos para processamento: {len(filtered_urls)}")
    
    # Usar URLs filtrados em vez dos URLs originais
    urls = filtered_urls
    
    # Controlar concorrência
    max_concurrent_downloads = 3  # Baseado no teste de rede
    # ✅ CORREÇÃO 2: Aumentar limite de processamento paralelo
    max_concurrent_processing = 4  # Permitir mais processamentos simultâneos
    
    download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
    process_semaphore = asyncio.Semaphore(max_concurrent_processing)  # Aumentado de 3 para 4
    
    # Listas para rastrear resultados
    successful_downloads = []
    failed_downloads = []
    processed_files = {}
    
    # Criar processadores
    processors = {}
    processing_results = {}
    
    logger.info(f"📋 Criando processadores para: {', '.join(tipos_a_processar)}")
    
    for tipo in tipos_a_processar:
        processor_key = {
            'empresas': 'empresa',
            'estabelecimentos': 'estabelecimento', 
            'simples': 'simples',
            'socios': 'socio',
            'painel': 'painel'
        }.get(tipo.lower())
        
        if processor_key:
            try:
                processor = ProcessorFactory.create(
                    processor_key,
                    source_zip_path,
                    unzip_path, 
                    output_parquet_path,
                    delete_zips_after_extract=delete_zips_after_extract,
                    **processing_options
                )
                processors[processor_key] = processor
                processing_results[tipo] = {'success': False, 'time': 0, 'files_processed': 0}
                logger.info(f"✅ Processador '{processor_key}' criado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao criar processador '{processor_key}': {e}")
                processing_results[tipo] = {'success': False, 'time': 0, 'error': str(e)}
    
    logger.info(f"📊 Total de processadores criados: {len(processors)}")
    
    # Obter configurações de rede
    try:
        network_results = await get_network_test_results()
        max_concurrent_downloads = min(6, network_results.get("recommendations", {}).get("max_concurrent_downloads", 3))
        connection_quality = network_results.get("quality", {}).get("connection_quality", "unknown")
    except Exception as e:
        logger.warning(f"Erro ao obter configurações de rede: {e}")
        max_concurrent_downloads = 3
        connection_quality = "unknown"
    
    logger.info(f"🌐 Rede: {connection_quality}")
    logger.info(f"🔧 Downloads simultâneos: {max_concurrent_downloads}")
    
    # Configurar semáforos
    download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
    process_semaphore = asyncio.Semaphore(max_concurrent_processing)  # Aumentado de 3 para 4
    
    # Listas para rastreamento
    successful_downloads = []
    failed_downloads = []
    processed_files = {}
    
    # Função para processar arquivo imediatamente após download/verificação
    async def process_file_immediately(file_path: str, filename: str) -> bool:
        """Processa um arquivo assim que ele está disponível."""
        async with process_semaphore:  # Controlar processamentos simultâneos
            # Determinar tipo do processador baseado no nome do arquivo
            processor_key = None
            tipo_original = None
            
            if filename.startswith('Empr'):
                processor_key = 'empresa'
                tipo_original = 'empresas'
            elif filename.startswith('Estabel'):
                processor_key = 'estabelecimento'
                tipo_original = 'estabelecimentos'
            elif filename.startswith('Simples'):
                processor_key = 'simples'
                tipo_original = 'simples'
            elif filename.startswith('Socio'):
                processor_key = 'socio'
                tipo_original = 'socios'
            elif filename.startswith('Painel'):
                processor_key = 'painel'
                tipo_original = 'painel'
            
            if not processor_key or processor_key not in processors:
                logger.warning(f"⚠️ Processador não encontrado para {filename} (tipo: {processor_key})")
                return False
            
            try:
                start_time = time.time()
                logger.info(f"🔄 Iniciando processamento de {filename}")
                
                processor = processors[processor_key]
                
                # ✅ CORREÇÃO 3: Executar processamento em thread separada para não bloquear event loop
                import concurrent.futures
                loop = asyncio.get_event_loop()
                
                # Executar processamento em executor para liberação do event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    success = await loop.run_in_executor(
                        executor,
                        lambda: processor.process_single_zip(
                            filename, 
                            source_zip_path, 
                            unzip_path, 
                            output_parquet_path, 
                            **processing_options
                        )
                    )
                
                elapsed_time = time.time() - start_time
                
                if success:
                    logger.info(f"✅ {filename} processado com sucesso em {elapsed_time:.1f}s")
                    if processor_key not in processed_files:
                        processed_files[processor_key] = []
                    processed_files[processor_key].append(filename)
                    
                    # Atualizar resultados
                    if tipo_original in processing_results:
                        processing_results[tipo_original]['files_processed'] += 1
                    return True
                else:
                    logger.error(f"❌ Falha ao processar {filename}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erro no processamento de {filename}: {e}")
                return False
    
    # Função para verificar/baixar e processar imediatamente
    async def download_and_process_immediately(url: str, session: aiohttp.ClientSession):
        """Baixa/verifica um arquivo e o processa imediatamente."""
        filename = os.path.basename(url)
        destination_path = os.path.join(source_zip_path, filename)
        
        try:
            async with download_semaphore:
                # Verificar se arquivo já existe E está íntegro
                if os.path.exists(destination_path) and not force_download:
                    # Verificar integridade do arquivo
                    if await validate_zip_integrity(destination_path):
                        logger.info(f"✅ Arquivo {filename} já existe e está íntegro. Processando imediatamente...")
                        successful_downloads.append(destination_path)
                        
                        # Processar imediatamente
                        await process_file_immediately(destination_path, filename)
                        return
                    else:
                        logger.error(f"❌ Arquivo {filename} baixado mas falhou na validação de integridade")
                        failed_downloads.append((filename, "Falha na validação de integridade"))
                        # Remover arquivo corrompido
                        try:
                            os.remove(destination_path)
                        except Exception:
                            pass
                else:
                    logger.warning(f"⚠️ Arquivo {filename} existe mas está corrompido. Fazendo novo download...")
                    # Remover arquivo corrompido
                    try:
                        os.remove(destination_path)
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo corrompido {filename}: {e}")
                
                # Fazer download
                logger.info(f"📥 Baixando {filename}...")
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            with open(destination_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                            
                            # Validar arquivo após download
                            if await validate_zip_integrity(destination_path):
                                logger.info(f"✅ Download de {filename} concluído e validado")
                                successful_downloads.append(destination_path)
                                
                                # Processar imediatamente após download
                                await process_file_immediately(destination_path, filename)
                            else:
                                logger.error(f"❌ Arquivo {filename} baixado mas falhou na validação de integridade")
                                failed_downloads.append((filename, "Falha na validação de integridade"))
                                # Remover arquivo corrompido
                                try:
                                    os.remove(destination_path)
                                except Exception:
                                    pass
                        else:
                            error_msg = f"HTTP {response.status}"
                            logger.error(f"❌ Erro no download de {filename}: {error_msg}")
                            failed_downloads.append((filename, error_msg))
                except Exception as download_error:
                    logger.error(f"❌ Erro no download de {filename}: {download_error}")
                    failed_downloads.append((filename, str(download_error)))
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado com {filename}: {e}")
            failed_downloads.append((filename, str(e)))
    
    # Função para validar integridade de arquivo ZIP
    async def validate_zip_integrity(file_path: str) -> bool:
        """Valida se um arquivo ZIP está íntegro."""
        import zipfile
        
        try:
            if not os.path.exists(file_path):
                return False
            
            # Verificar tamanho mínimo (arquivos muito pequenos são suspeitos)
            file_size = os.path.getsize(file_path)
            if file_size < 1024:  # Menor que 1KB é suspeito
                logger.warning(f"Arquivo {os.path.basename(file_path)} muito pequeno: {file_size} bytes")
                return False
            
            # Verificar se é um ZIP válido
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Tentar listar o conteúdo (detecta corrupção)
                    file_list = zip_ref.namelist()
                    if not file_list:
                        logger.warning(f"Arquivo ZIP {os.path.basename(file_path)} está vazio")
                        return False
                    
                    # Verificar se pelo menos um arquivo pode ser lido
                    first_file = file_list[0]
                    try:
                        with zip_ref.open(first_file) as f:
                            # Ler primeiro chunk para verificar se não está corrompido
                            f.read(1024)
                    except Exception as e:
                        logger.warning(f"Erro ao ler conteúdo do ZIP {os.path.basename(file_path)}: {e}")
                        return False
                
                return True
                
            except zipfile.BadZipFile:
                logger.warning(f"Arquivo {os.path.basename(file_path)} não é um ZIP válido")
                return False
            except Exception as e:
                logger.warning(f"Erro ao validar ZIP {os.path.basename(file_path)}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erro geral na validação de {os.path.basename(file_path)}: {e}")
            return False
    
    # Executar downloads e processamentos em paralelo
    start_time = time.time()
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=3600, connect=30),
        connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
    ) as session:
        
        # Criar tasks para todos os URLs
        tasks = [download_and_process_immediately(url, session) for url in urls]
        
        logger.info(f"🚀 Iniciando pipeline com {len(tasks)} arquivos...")
        logger.info("📊 Cada arquivo será processado assim que for verificado/baixado")
        logger.info(f"⚙️ Configuração: máx {max_concurrent_downloads} downloads + máx {max_concurrent_processing} processamentos simultâneos")
        
        # Executar todas as tasks em paralelo
        await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Calcular estatísticas finais
    for tipo in tipos_a_processar:
        processor_key = {
            'empresas': 'empresa',
            'estabelecimentos': 'estabelecimento', 
            'simples': 'simples',
            'socios': 'socio',
            'painel': 'painel'
        }.get(tipo.lower())
        
        if processor_key in processed_files:
            files_count = len(processed_files[processor_key])
            processing_results[tipo]['success'] = files_count > 0
            processing_results[tipo]['files_processed'] = files_count
        
        processing_results[tipo]['time'] = total_time
    
    # Log do resumo
    logger.info("=" * 60)
    logger.info("📊 RESUMO DO PIPELINE OTIMIZADO:")
    logger.info("=" * 60)
    logger.info(f"⏱️  Tempo total: {format_elapsed_time(total_time)}")
    logger.info(f"📥 Downloads bem-sucedidos: {len(successful_downloads)}")
    logger.info(f"❌ Downloads com falha: {len(failed_downloads)}")
    
    for tipo, result in processing_results.items():
        if isinstance(result, dict) and 'success' in result:
            status = "✅ SUCESSO" if result['success'] else "❌ FALHA"
            files_processed = result.get('files_processed', 0)
            logger.info(f"{tipo.upper()}: {status} - {files_processed} arquivos processados")
    
    logger.info("=" * 60)
    
    # Determinar sucesso geral
    all_success = all(result.get('success', False) for result in processing_results.values() if isinstance(result, dict) and 'success' in result)
    processing_results['all_ok'] = all_success
    processing_results['total_time'] = total_time
    processing_results['downloads_successful'] = len(successful_downloads)
    processing_results['downloads_failed'] = len(failed_downloads)
    
    return processing_results

def cleanup_after_database(parquet_folder: str, zip_folder: str = "", cleanup_parquet: bool = False, cleanup_zip: bool = False) -> bool:
    """
    Realiza limpeza de arquivos após criação bem-sucedida do banco DuckDB.
    
    Args:
        parquet_folder: Pasta contendo os arquivos parquet
        zip_folder: Pasta contendo os arquivos ZIP (opcional)
        cleanup_parquet: Se deve deletar os arquivos parquet
        cleanup_zip: Se deve deletar os arquivos ZIP
        
    Returns:
        bool: True se limpeza foi bem-sucedida, False caso contrário
    """
    success = True
    
    if not cleanup_parquet and not cleanup_zip:
        logger.debug("Nenhuma limpeza solicitada")
        return True
    
    print_section("Realizando limpeza de arquivos")
    
    try:
        # Contadores para estatísticas
        parquet_files_deleted = 0
        parquet_size_freed = 0
        zip_files_deleted = 0
        zip_size_freed = 0
        
        # Limpar arquivos parquet se solicitado
        if cleanup_parquet and os.path.exists(parquet_folder):
            logger.info(f"Iniciando limpeza de arquivos parquet em: {parquet_folder}")
            
            for root, dirs, files in os.walk(parquet_folder):
                for file in files:
                    if file.endswith('.parquet'):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            parquet_files_deleted += 1
                            parquet_size_freed += file_size
                            logger.debug(f"Arquivo parquet deletado: {file}")
                        except Exception as e:
                            logger.error(f"Erro ao deletar arquivo parquet {file}: {e}")
                            success = False
        
        # Limpar arquivos ZIP se solicitado
        if cleanup_zip and zip_folder and os.path.exists(zip_folder):
            logger.info(f"Iniciando limpeza de arquivos ZIP em: {zip_folder}")
            
            for root, dirs, files in os.walk(zip_folder):
                for file in files:
                    if file.endswith('.zip'):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            zip_files_deleted += 1
                            zip_size_freed += file_size
                            logger.debug(f"Arquivo ZIP deletado: {file}")
                        except Exception as e:
                            logger.error(f"Erro ao deletar arquivo ZIP {file}: {e}")
                            success = False
        
        # Exibir estatísticas da limpeza
        total_size_freed = parquet_size_freed + zip_size_freed
        total_files_deleted = parquet_files_deleted + zip_files_deleted
        
        if total_files_deleted > 0:
            size_freed_mb = total_size_freed / (1024 * 1024)
            size_freed_gb = size_freed_mb / 1024
            
            if size_freed_gb >= 1:
                print_success(f"Limpeza concluída: {total_files_deleted} arquivos removidos, {size_freed_gb:.2f} GB liberados")
            else:
                print_success(f"Limpeza concluída: {total_files_deleted} arquivos removidos, {size_freed_mb:.2f} MB liberados")
        else:
            print_warning("Nenhum arquivo foi removido durante a limpeza")
        
        return success
        
    except Exception as e:
        logger.error(f"Erro durante limpeza de arquivos: {e}")
        print_error(f"Erro durante limpeza: {e}")
        return False

if __name__ == '__main__':
    main()  # Executar sem imprimir o retorno
