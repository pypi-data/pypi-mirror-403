# Notion SDK

> **Beta Release** 🎉\
> Desenvolvido por [Eduardo Riguetto](https://riguetto.dev)

## 🎯 Visão Geral

SDK Python moderno e type-safe para a API Notion, com foco em Developer Experience (DX) e autocomplete perfeito.

---

## ✨ Principais Features

### 🔐 Autenticação Simplificada

- Configuração centralizada via `Notion()` com suporte a múltiplas versões da API
- Suporte para versões `legacy` (2022-06-28), `data_sources` (2025-09-03), ou personalizada
- Headers gerenciados automaticamente via singleton pattern

### 🗄️ ORM Declarativo

- **Sistema de Mapeamento Declarativo**: Defina schemas uma única vez com `NotionDatabase`
- **Type Hints Perfeitos**: Autocomplete completo em IDEs (VSCode, PyCharm)
- **Transformers Customizáveis**: Processe propriedades do Notion conforme necessário
- **Validators Integrados**: Validação automática com Pydantic
- **Computed Fields**: Campos calculados automaticamente a partir de outros campos
- **Registry Global**: Acesso centralizado a todas as databases via `DatabaseRegistry`
- **Container Pattern**: Organize suas databases com `DatabasesContainer`

### 📦 Repositories

**Pages:**

- `CreatePage` - Criação de páginas com fluent interface
- `GetPage` - Busca de páginas com mapeamento automático de schemas
- `GetPageProperty` - Acesso direto a propriedades específicas

**Databases:**

- `CreateDatabasePage` - Criação de páginas em databases com type safety
- `SearchPage` - Queries avançadas com filtros e ordenação
- `SearchPageProperty` - Busca de propriedades específicas em databases

### 🎨 Fluent Interface

```python
await notion.orm.repo.pages.CreatePage()\
    .set_parent("database_id", "db_id")\
    .set_title("Name", "My Page")\
    .set_property.start_date("Date", datetime.now())\
    .set_property.number("Count", 42)\
    .call()
```

### 🔧 Features Avançadas

- **Generic Types**: Tipagem forte com Generic/TypeVars para autocomplete perfeito
- **Property System**: Sistema completo de setters para todos os tipos de propriedades
- **Query Builders**: Construtores fluentes para filtros (`QueryFilter`) e ordenação (`QuerySort`)
- **Property Extractors**: Extração automática de propriedades da API Notion
- **Property Parsers**: Parse inteligente de respostas com suporte a tipos complexos
- **Property Accessors**: Acesso tipado a propriedades de páginas
- **Configuração Global**: Timezone e outras configs definidas via `ORMConfig`
- **Singleton Pattern**: Client configurado globalmente, sem duplicação

---

## 🚀 Quick Start

```python
from notion import Notion
from my_databases import MyContainer

# Configuração
notion: Notion[MyContainer] = Notion(
    api_token="secret_...",
    api_version="data_sources",
    orm_container=MyContainer,
    timezone="America/Sao_Paulo"
)

# Uso com autocomplete perfeito
con = notion.orm.repo.databases.container.tasks.SearchPage
result = await con\
    .set_filter(
        con.filter.checkbox("Done", "equals", False)
    )\
    .call()

# Acesso type-safe
for page in result.results:
    print(page.properties.myproperty)  # ← Autocomplete funciona!
```

---

### 📦 Configurando seu ORM

#### 1. Defina seus Schemas

Crie schemas para suas databases do Notion usando `NotionDatabase`:

```python
# my_databases/tasks.py

from notion.types.orm.databases import NotionDatabase
from pydantic import ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class TasksDb(NotionDatabase):
    
    model_config = ConfigDict(title="Notion_Databases_TasksDb")
    
    # Defina os campos do schema
    title: Optional[str]
    status: Optional[str]
    priority: Optional[str]
    tags: Optional[List[str]]
    due_date: Optional[date]
    assignee: Optional[str]
    completed: bool = False
    progress: Optional[int]
    estimated_hours: Optional[Decimal]
    actual_hours: Optional[Decimal]
    
    # Campos computed (não vêm do Notion, são calculados)
    is_overdue: Optional[bool] = None
    total_cost: Optional[Decimal] = None
    
    class NotionConfig:
        # ID da sua database no Notion
        database_id = "abc123def456"
        
        # Mapeie campos Python → Campos Notion
        mappings = {
            "title": "Title",
            "status": "Status",
            "priority": "Priority",
            "tags": "Tags",
            "due_date": "Due Date",
            "assignee": "Assignee",
            "completed": "Completed",
            "progress": "Progress",
            "estimated_hours": "Estimated Hours",
            "actual_hours": "Actual Hours"
        }
        
        # Transformers para processar valores
        transformers = {
            "status": lambda x: x["name"] if x else None,
            "priority": lambda x: x["name"] if x else None,
            "tags": lambda x: [t["name"] for t in x] if x else [],
            "assignee": lambda x: x[0] if x else None,
            "due_date": lambda x: x["start"] if x else None,
            "estimated_hours": lambda x: Decimal(str(x)) if x else None,
            "actual_hours": lambda x: Decimal(str(x)) if x else None
        }
        
        # Validators para garantir integridade dos dados
        validators = {
            "progress": lambda v: max(0, min(100, v)) if v else 0,  # Entre 0-100
            "estimated_hours": lambda v: v if v and v >= 0 else Decimal(0)  # Não negativo
        }
        
        # Computed fields calculados automaticamente
        computed = {
            "is_overdue": lambda obj: (
                obj.due_date < date.today() and not obj.completed
                if obj.due_date else False
            ),
            "total_cost": lambda obj: (
                obj.actual_hours * Decimal("50.00")  # $50/hora
                if obj.actual_hours else None
            )
        }
```

#### 2. Crie seu Container

Organize todas as suas databases em um container:

```python
# my_databases/__init__.py

from notion.types.orm.databases import Container, Registry, Client
from .tasks import TasksDb
from .projects import ProjectsDb  # Outras databases...

class MyDatabasesContainer(Container):
    """Container customizado com suas databases"""
    
    def __init__(self):
        # Registre todas as databases
        Registry.register(TasksDb)
        Registry.register(ProjectsDb)
        
        # Configure acesso tipado
        self.tasks: Client[TasksDb] = Client(TasksDb.id())
        self.projects: Client[ProjectsDb] = Client(ProjectsDb.id())

# Singleton para uso direto
databases = MyDatabasesContainer()

__all__ = ["MyDatabasesContainer", "databases"]
```

#### 3. Configure a Integração

No seu `main.py` ou arquivo de inicialização:

```python
from notion import Notion
from my_databases import MyDatabasesContainer

# Configure com seu container
notion = Notion(
    api_token="secret_...",
    api_version="data_sources",
    orm_container=MyDatabasesContainer,
    timezone="America/Sao_Paulo"
)

# Agora você tem autocomplete perfeito!
con = notion.orm.repo.databases.container.tasks.SearchPage
tasks = await con\
    .set_filter(
        con.checkbox("Completed", "equals", False)
    )\
    .call()

# Acesso type-safe aos dados
for task in tasks.results:
    print(f"📋 {task.properties.title}")
    print(f"Status: {task.properties.status}")
    print(f"Due: {task.properties.due_date}")
```

---

## 📚 Client API

### Pages

- `get(page_id)` - Buscar página por ID
- `get_property(page_id, property_id)` - Buscar propriedade específica
- `update_properties(page_id, properties)` - Atualizar propriedades de uma página
- `create(parent, properties)` - Criar nova página

### Databases

- `get(database_id)` - Buscar informações de uma database
- `query(database_id, filter, sorts)` - Query com filtros e ordenação
- `query_property(database_id, property_id)` - Query propriedade específica
- `update(database_id, properties)` - Atualizar schema de database

### Blocks

- `get_children(block_id)` - Buscar blocos filhos de um bloco/página

---

## 📖 Schemas Disponíveis

**Responses:**

- `pages.Page`, `pages.Parent` - Estruturas de páginas
- `databases.Query` - Resultados de queries
- `users.User`, `users.Person`, `users.Bot` - Informações de usuários
- `errors.Error` - Erros da API
- `pages.properties.RichText` - Propriedade rich text

**ORM:**

- `NotionDatabase` - Classe base para schemas customizados
- `DatabasesContainer` - Container para organização de databases
- `SearchPageProperty` - Schema para propriedades de busca
- `properties.RichText` - Rich text para ORM

**DTO:**

- Data Transfer Objects para comunicação interna

---

## 🏗️ Arquitetura

```
notion/
├── auth/               # Sistema de autenticação
├── client/             # HTTP clients por endpoint
│   ├── blocks.py       # Blocks API
│   ├── databases.py    # Databases API
│   └── pages.py        # Pages API
├── orm/
│   ├── accessors/      # Acesso tipado a propriedades
│   ├── common/         # QueryFilter, QuerySort, SetProperty
│   ├── config/         # Configurações globais do ORM
│   ├── extractors/     # Extração de propriedades da API
│   ├── mapping/        # Sistema declarativo (NotionDatabase)
│   ├── parsers/        # Parse de respostas da API
│   └── repositories/   # Camada de repositórios
│       ├── databases/  # Repositórios de databases
│       └── pages/      # Repositórios de pages
├── schemas/
│   ├── orm/            # Schemas do ORM
│   │   ├── database/   # DatabasesContainer, SearchPageProperty
│   │   └── properties/ # RichText e outros
│   └── responses/      # Schemas de respostas da API
│       ├── databases/  # Query
│       ├── errors/     # Error
│       ├── pages/      # Page, Parent, properties
│       └── users/      # User, Person, Bot
└── types/              # Type definitions e exports
    ├── orm/            # Types do ORM
    └── responses/      # Types de responses
```

---

## 📋 Dependências

- Python >= 3.9
- httpx - Requests HTTP assíncronos
- pydantic >= 2.5 - Validação e serialização

---

## 🐛 Known Issues

- Suporte parcial a tipos de propriedades (em desenvolvimento contínuo)
- Documentação completa em progresso
- Alguns endpoints da API Notion ainda não implementados

---

## 🔮 Roadmap

- [ ] Support completo para Blocks API (criação e atualização)
- [ ] Suporte completo a todos os tipos de propriedades Notion
- [ ] Documentação completa com exemplos práticos
- [ ] Testes unitários e de integração
- [ ] Support para Comments API
- [ ] Cache system para reduzir chamadas à API
- [ ] Retry logic e rate limiting inteligente
- [ ] CLI para geração automática de schemas a partir de databases

---

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes

---

## 🙏 Agradecimentos

Desenvolvido com ❤️ por [Eduardo Riguetto](https://riguetto.dev)

**Contribuições são bem-vindas!** Sinta-se livre para:

- 🐛 Reportar bugs via Issues
- 💡 Sugerir features
- 🔧 Abrir Pull Requests
- 📖 Melhorar a documentação

---

## 🔗 Links

- **GitHub**: [https://github.com/riguettodev/sdk-notion](https://github.com/riguettodev/sdk-notion)
- **PyPI**: [https://pypi.org/project/sdk-notion/](https://pypi.org/project/sdk-notion/)
- **Documentação**: (em breve)
