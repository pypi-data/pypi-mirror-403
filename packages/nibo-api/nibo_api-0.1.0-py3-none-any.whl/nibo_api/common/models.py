"""
Modelos de dados compartilhados para a API Nibo
"""
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime


@dataclass
class CategoryElement:
    """Elemento de categoria em um agendamento"""
    id: UUID
    category_id: UUID
    category_name: str
    value: float
    description: str
    type: str
    parent: str
    parent_id: UUID
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryElement':
        """Cria instância a partir de dicionário"""
        return cls(
            id=UUID(data["id"]),
            category_id=UUID(data["categoryId"]),
            category_name=data["categoryName"],
            value=float(data["value"]),
            description=data.get("description", ""),
            type=data["type"],
            parent=data.get("parent", ""),
            parent_id=UUID(data["parentId"]) if data.get("parentId") else UUID('00000000-0000-0000-0000-000000000000')
        )


@dataclass
class Stakeholder:
    """Stakeholder (cliente, fornecedor, funcionário, sócio)"""
    id: UUID
    name: str
    is_deleted: bool
    type: str
    cpf_cnpj: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stakeholder':
        """Cria instância a partir de dicionário"""
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            is_deleted=data.get("isDeleted", False),
            type=data["type"],
            cpf_cnpj=data.get("cpfCnpj")
        )


@dataclass
class Recurrence:
    """Configuração de recorrência de agendamento"""
    id: UUID
    interval: int
    interval_type: int
    interval_type_description: str
    end_type: int
    end_type_description: str
    provision_in_advance: int
    base_day: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recurrence':
        """Cria instância a partir de dicionário"""
        return cls(
            id=UUID(data["id"]),
            interval=data["interval"],
            interval_type=data["intervalType"],
            interval_type_description=data["intervalTypeDescription"],
            end_type=data["endType"],
            end_type_description=data["endTypeDescription"],
            provision_in_advance=data.get("provisionInAdvance", 0),
            base_day=data.get("baseDay", 0)
        )


@dataclass
class AgendamentoRecebimento:
    """Agendamento de recebimento (conta a receber)"""
    schedule_id: UUID
    type: str
    is_entry: bool
    is_bill: bool
    is_debit_note: bool
    is_flagged: bool
    is_dued: bool
    due_date: datetime
    accrual_date: datetime
    schedule_date: datetime
    create_date: datetime
    create_user: str
    update_date: datetime
    update_user: str
    value: float
    is_paid: bool
    cost_center_value_type: int
    paid_value: float
    open_value: float
    stakeholder_id: UUID
    stakeholder: Stakeholder
    description: str
    reference: str
    category: Stakeholder
    has_installment: bool
    has_recurrence: bool
    categories: List[CategoryElement] = field(default_factory=list)
    cost_centers: List[Any] = field(default_factory=list)
    recurrence: Optional[Recurrence] = None
    has_open_entry_promise: bool = False
    has_entry_promise: bool = False
    auto_generate_entry_promise: bool = False
    has_invoice: bool = False
    has_pending_invoice: bool = False
    has_schedule_invoice: bool = False
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    auto_generate_nf_se_type: int = 0
    is_payment_scheduled: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgendamentoRecebimento':
        """Cria instância a partir de dicionário"""
        # Parse de datas
        def parse_datetime(dt_str: str) -> datetime:
            if isinstance(dt_str, datetime):
                return dt_str
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
        categories = [
            CategoryElement.from_dict(cat) 
            for cat in data.get("categories", [])
        ]
        
        recurrence = None
        if data.get("hasRecurrence") and data.get("recurrence"):
            recurrence = Recurrence.from_dict(data["recurrence"])
        
        return cls(
            schedule_id=UUID(data["scheduleId"]),
            type=data["type"],
            is_entry=data.get("isEntry", False),
            is_bill=data.get("isBill", False),
            is_debit_note=data.get("isDebitNote", False),
            is_flagged=data.get("isFlagged", False),
            is_dued=data.get("isDued", False),
            due_date=parse_datetime(data["dueDate"]),
            accrual_date=parse_datetime(data["accrualDate"]),
            schedule_date=parse_datetime(data["scheduleDate"]),
            create_date=parse_datetime(data["createDate"]),
            create_user=data["createUser"],
            update_date=parse_datetime(data["updateDate"]),
            update_user=data["updateUser"],
            value=float(data["value"]),
            is_paid=data.get("isPaid", False),
            cost_center_value_type=data.get("costCenterValueType", 0),
            paid_value=float(data.get("paidValue", 0)),
            open_value=float(data.get("openValue", 0)),
            stakeholder_id=UUID(data.get("stakeholderId", "00000000-0000-0000-0000-000000000000")),
            stakeholder=Stakeholder.from_dict(data["stakeholder"]),
            description=data.get("description", ""),
            reference=data.get("reference", ""),
            category=Stakeholder.from_dict(data["category"]),
            has_installment=data.get("hasInstallment", False),
            has_recurrence=data.get("hasRecurrence", False),
            categories=categories,
            cost_centers=data.get("costCenters", []),
            recurrence=recurrence,
            has_open_entry_promise=data.get("hasOpenEntryPromise", False),
            has_entry_promise=data.get("hasEntryPromise", False),
            auto_generate_entry_promise=data.get("autoGenerateEntryPromise", False),
            has_invoice=data.get("hasInvoice", False),
            has_pending_invoice=data.get("hasPendingInvoice", False),
            has_schedule_invoice=data.get("hasScheduleInvoice", False),
            custom_attributes=data.get("customAttributes", {}),
            auto_generate_nf_se_type=data.get("autoGenerateNFSeType", 0),
            is_payment_scheduled=data.get("isPaymentScheduled", False)
        )


@dataclass
class AgendamentoList:
    """Lista paginada de agendamentos"""
    items: List[AgendamentoRecebimento]
    count: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgendamentoList':
        """Cria instância a partir de dicionário"""
        items = [
            AgendamentoRecebimento.from_dict(item)
            for item in data.get("items", [])
        ]
        return cls(
            items=items,
            count=data.get("count", len(items))
        )


@dataclass
class Cliente:
    """Cliente do Nibo"""
    id: UUID
    name: str
    is_deleted: bool
    type: str
    document: Optional[Dict[str, Any]] = None
    communication: Optional[Dict[str, Any]] = None
    address: Optional[Dict[str, Any]] = None
    bank_account_information: Optional[Dict[str, Any]] = None
    company_information: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cliente':
        """Cria instância a partir de dicionário"""
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            is_deleted=data.get("isDeleted", False),
            type=data.get("type", "Customer"),
            document=data.get("document"),
            communication=data.get("communication"),
            address=data.get("address"),
            bank_account_information=data.get("bankAccountInformation"),
            company_information=data.get("companyInformation")
        )


@dataclass
class Categoria:
    """Categoria de agendamento"""
    id: UUID
    name: str
    type: str
    is_deleted: bool = False
    parent_id: Optional[UUID] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Categoria':
        """Cria instância a partir de dicionário"""
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            type=data.get("type", ""),
            is_deleted=data.get("isDeleted", False),
            parent_id=UUID(data["parentId"]) if data.get("parentId") else None
        )


@dataclass
class CategoriaList:
    """Lista de categorias"""
    items: List[Categoria]
    count: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoriaList':
        """Cria instância a partir de dicionário"""
        items = [
            Categoria.from_dict(item)
            for item in data.get("items", [])
        ]
        return cls(
            items=items,
            count=data.get("count", len(items))
        )

