from dotenv import load_dotenv
from flask import Blueprint, jsonify

from models import (
    CentroCustos,
    Client,
    Client_by_CC,
    Clock_Client,
    Clock_Project,
    Clock_tag,
    Clock_Time_Entry,
    Clock_User,
    ContaPagamento,
    Contexted_hour_entry,
    Extrato,
    Pedido,
    PrimaData,
    Relatorio_CC,
    ServiceOrder,
    db,
)

load_dotenv()

tables_statistcs_route = Blueprint("TABLE_STATISTIC", __name__)


def get_row_count_with_filter(model, query_params):
    try:
        query = db.session.query(model)

        for key, value in query_params.items():
            # Assuming keys in query_params match column names in your model
            column = getattr(model, key, None)
            if column is not None:
                query = query.filter(column == value)

        row_count = query.count()
        return row_count
    except Exception as e:
        print(f"Error: {e}")
        return -1


def get_table_statistic():
    CENTRO_CUSTOS_ATIVOS = get_row_count_with_filter(CentroCustos, {})
    CENTRO_CUSTOS_EXCLUIDOS = get_row_count_with_filter(
        CentroCustos, {"lixeira": "Sim", "status_centro_custo": "Inativo"}
    )
    CLIENTES_ATIVOS = get_row_count_with_filter(Client, {})
    CLIENTES_EXCLUIDOS = get_row_count_with_filter(Client, {"lixeira": "Sim"})
    get_row_count_with_filter(Client_by_CC, {})
    CLOCK_CLIENT = get_row_count_with_filter(Clock_Client, {})
    CLOCK_PROJECT = get_row_count_with_filter(Clock_Project, {})
    CLOCK_TAG = get_row_count_with_filter(Clock_tag, {})
    CLOCK_TIME_ENTRY = get_row_count_with_filter(Clock_Time_Entry, {})
    CLOCK_USER = get_row_count_with_filter(Clock_User, {})
    CONTA_PAGAMENTO_ATIVA = get_row_count_with_filter(ContaPagamento, {})
    CONTA_PAGAMENTO_EXCLUIDOS = get_row_count_with_filter(
        ContaPagamento, {"liquidado_pag": "Sim"}
    )
    CONTEXTED_HOUR_ENTRY = get_row_count_with_filter(Contexted_hour_entry, {})
    EXTRATO_ATIVOS = get_row_count_with_filter(Extrato, {})
    EXTRATOS_EXCLUIDOS = get_row_count_with_filter(Extrato, {"lixeira": "Sim"})
    PEDIDO_ATIVO = get_row_count_with_filter(Pedido, {})
    PEDIDO_EXCLUIDOS = get_row_count_with_filter(Pedido, {"lixeira": "Sim"})
    PRIMA_DATA = get_row_count_with_filter(PrimaData, {})
    RELATORIO_CC = get_row_count_with_filter(Relatorio_CC, {})
    # RELATORO_DESPESAS = get_row_count_with_filter(Relatorio_Despesas, {})
    # RELATORIO_HORAS = get_row_count_with_filter(Relatorio_Horas, {})
    SERVICE_ORDER_ATIVOS = get_row_count_with_filter(ServiceOrder, {})
    SERVICE_ORDER_EXCLUIDOS = get_row_count_with_filter(
        ServiceOrder, {"lixeira": "Sim"}
    )

    return {
        "centro_custos_ativos": CENTRO_CUSTOS_ATIVOS,
        "centro_custos_excluidos": CENTRO_CUSTOS_EXCLUIDOS,
        "clientes_ativos": CLIENTES_ATIVOS,
        "clientes_excluidos": CLIENTES_EXCLUIDOS,
        # "clientes_by_cc": CLIENTES_BY_CC,
        "clock_client": CLOCK_CLIENT,
        "clock_project": CLOCK_PROJECT,
        "clock_tag": CLOCK_TAG,
        "clock_time_entry": CLOCK_TIME_ENTRY,
        "clock_user": CLOCK_USER,
        "conta_pagamento_ativa": CONTA_PAGAMENTO_ATIVA,
        "conta_pagamento_excluidos": CONTA_PAGAMENTO_EXCLUIDOS,
        "contexted_hour_entry": CONTEXTED_HOUR_ENTRY,
        "extrato_ativos": EXTRATO_ATIVOS,
        "extratos_excluidos": EXTRATOS_EXCLUIDOS,
        "pedido_ativo": PEDIDO_ATIVO,
        "pedido_excluidos": PEDIDO_EXCLUIDOS,
        "prima_data": PRIMA_DATA,
        "relatorio_cc": RELATORIO_CC,
        # "relatoro_despesas": RELATORO_DESPESAS,
        # "relatorio_horas": RELATORIO_HORAS,
        "service_order_ativos": SERVICE_ORDER_ATIVOS,
        "service_order_excluidos": SERVICE_ORDER_EXCLUIDOS,
    }


@tables_statistcs_route.route("/statistic/count", methods=["GET"])
def statistic_update():
    try:
        counts = get_table_statistic()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(counts), 201
