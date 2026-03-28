import json
import os
import re
from datetime import datetime

from models import NF, db
from VHSYS.api import api_results


def is_valid_date_string(date_string):
    if date_string != "0000-00-00 00:00:00":
        return date_string
    return None


def verify_numeric_float(number):
    if isinstance(number, float):
        return number
    return float(number)


def verify_numeric_int(number):
    if number == "":
        return -1
    if not number:
        return -1
    if number is None:
        return -1
    try:
        number_as_int = int(number)
        return number_as_int
    except (ValueError, TypeError):
        return -1


def status_centro_custo(status):
    if status == "Ativo":
        return True
    return False


def status_lixeira(status):
    if status == "Sim":
        return True
    return False


def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return -1


def format_float(value):
    if value is None:
        return format(0.0, ".2f")
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            # trunk-ignore(ruff/B904)
            raise ValueError(
                "The input value is not a valid float or string representation of a float."
            )

    if isinstance(value, float):
        return format(value, ".2f")
    else:
        raise ValueError(
            "The input value is not a valid float or string representation of a float."
        )


def create_nf(data):
    new_nf = NF(
        id_venda=data["id_venda"],
        tp_nfe=data["tp_nfe"],
        serie_nota=data["serie_nota"],
        id_pedido=data["id_pedido"],
        id_cliente=data["id_cliente"],
        nome_cliente=data["nome_cliente"],
        vendedor_pedido=data["vendedor_pedido"],
        vendedor_pedido_id=data["vendedor_pedido_id"],
        valor_total_produtos=data["valor_total_produtos"],
        desconto_pedido=data["desconto_pedido"],
        peso_total_nota=data["peso_total_nota"],
        peso_total_nota_liq=data["peso_total_nota_liq"],
        frete_pedido=data["frete_pedido"],
        valor_total_nota=data["valor_total_nota"],
        valor_baseICMS=data["valor_baseICMS"],
        valor_ICMS=data["valor_ICMS"],
        valor_baseST=data["valor_baseST"],
        valor_ST=data["valor_ST"],
        valor_IPI=data["valor_IPI"],
        valor_despesas=data["valor_despesas"],
        condicao_pagamento=data["condicao_pagamento"],
        transportadora_pedido=data["transportadora_pedido"],
        id_transportadora=data["id_transportadora"],
        frete_por_pedido=data["frete_por_pedido"],
        volumes_transporta=data["volumes_transporta"],
        especie_transporta=data["especie_transporta"],
        marca_transporta=data["marca_transporta"],
        numeracao_transporta=data["numeracao_transporta"],
        placa_transporta=data["placa_transporta"],
        uf_embarque=data["uf_embarque"],
        local_embarque=data["local_embarque"],
        data_pedido=data["data_pedido"],
        data_pedido_hora=data["data_pedido_hora"],
        data_emissao=data["data_emissao"],
        natureza_pedido=data["natureza_pedido"],
        finalidade_nfe=data["finalidade_nfe"],
        obs_pedido=data["obs_pedido"],
        obs_interno_pedido=data["obs_interno_pedido"],
        status_pedido=data["status_pedido"],
        contas_pedido=data["contas_pedido"],
        comissao_pedido=data["comissao_pedido"],
        boletos_pedido=data["boletos_pedido"],
        estoque_pedido=data["estoque_pedido"],
        nota_emitida=data["nota_emitida"],
        nota_chave=data["nota_chave"],
        nota_protocolo=data["nota_protocolo"],
        nota_codigov=data["nota_codigov"],
        nota_recibo=data["nota_recibo"],
        nota_data_autorizacao=data["nota_data_autorizacao"],
        nota_usuario_autorizacao=data["nota_usuario_autorizacao"],
        nota_data_cancelamento=is_valid_date_string(data["nota_data_cancelamento"]),
        nota_usuario_cancelamento=is_valid_date_string(
            data["nota_usuario_cancelamento"]
        ),
        nota_motivo_cancelamento=data["nota_motivo_cancelamento"],
        nota_denegada=is_valid_date_string(data["nota_denegada"]),
        nota_importada=is_valid_date_string(data["nota_importada"]),
        nota_scan=is_valid_date_string(data["nota_scan"]),
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        ambiente=data["ambiente"],
        lixeira=data["lixeira"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_nf)
    db.session.commit()


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def get_element_by_id(id):
    return db.session.query(NF).filter_by(id_venda=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_element_by_id(id)

    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    existing_element.updated_at = datetime.utcnow()

    db.session.commit()

    return existing_element


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            ref_reg_db = reg_db[key]
            ref_reg_api = reg_api[key]
            print(
                f"(DIVERGENCES) DB {ref_reg_db} <-> API {ref_reg_api} ,({key}",
                flush=True,
            )
            return True
    return False


class VHSYS_NF:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/notas-fiscais"
        self.api_elements = []
        self.db_elements = []
        self.all = []

    def verify_elements(self):
        registers = api_results(self.url)
        for register in registers:
            register_dict = {
                "id_venda": register["id_venda"],
                "tp_nfe": register["tp_nfe"],
                "serie_nota": register["serie_nota"],
                "id_pedido": register["id_pedido"],
                "id_cliente": register["id_cliente"],
                "nome_cliente": register["nome_cliente"],
                "vendedor_pedido": register["vendedor_pedido"],
                "vendedor_pedido_id": register["vendedor_pedido_id"],
                "valor_total_produtos": register["valor_total_produtos"],
                "desconto_pedido": register["desconto_pedido"],
                "peso_total_nota": register["peso_total_nota"],
                "peso_total_nota_liq": register["peso_total_nota_liq"],
                "frete_pedido": register["frete_pedido"],
                "valor_total_nota": register["valor_total_nota"],
                "valor_baseICMS": register["valor_baseICMS"],
                "valor_ICMS": register["valor_ICMS"],
                "valor_baseST": register["valor_baseST"],
                "valor_ST": register["valor_ST"],
                "valor_IPI": register["valor_IPI"],
                "valor_despesas": register["valor_despesas"],
                "condicao_pagamento": register["condicao_pagamento"],
                "transportadora_pedido": register["transportadora_pedido"],
                "id_transportadora": register["id_transportadora"],
                "frete_por_pedido": int(register["frete_por_pedido"]),
                "volumes_transporta": register["volumes_transporta"],
                "especie_transporta": register["especie_transporta"],
                "marca_transporta": register["marca_transporta"],
                "numeracao_transporta": register["numeracao_transporta"],
                "placa_transporta": register["placa_transporta"],
                "uf_embarque": register["uf_embarque"],
                "local_embarque": register["local_embarque"],
                "data_pedido": register["data_pedido"],
                "data_pedido_hora": register["data_pedido_hora"],
                "data_emissao": register["data_emissao"],
                "natureza_pedido": register["natureza_pedido"],
                "finalidade_nfe": register["finalidade_nfe"],
                "obs_pedido": register["obs_pedido"],
                "obs_interno_pedido": register["obs_interno_pedido"],
                "status_pedido": register["status_pedido"],
                "contas_pedido": int(register["contas_pedido"]),
                "comissao_pedido": register["comissao_pedido"],
                "boletos_pedido": register["boletos_pedido"],
                "estoque_pedido": register["estoque_pedido"],
                "nota_emitida": register["nota_emitida"],
                "nota_chave": register["nota_chave"],
                "nota_protocolo": register["nota_protocolo"],
                "nota_codigov": register["nota_codigov"],
                "nota_recibo": register["nota_recibo"],
                "nota_data_autorizacao": register["nota_data_autorizacao"],
                "nota_usuario_autorizacao": register["nota_usuario_autorizacao"],
                "nota_data_cancelamento": register["nota_data_cancelamento"],
                "nota_usuario_cancelamento": register["nota_usuario_cancelamento"],
                "nota_motivo_cancelamento": register["nota_motivo_cancelamento"],
                "nota_denegada": register["nota_denegada"],
                "nota_importada": register["nota_importada"],
                "nota_scan": register["nota_scan"],
                "data_cad_pedido": register["data_cad_pedido"],
                "data_mod_pedido": register["data_mod_pedido"],
                "ambiente": register["ambiente"],
                "lixeira": register["lixeira"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = NF.query.all()
        for register in registers_db:
            register_dict = {
                "id_venda": register.id_venda,
                "tp_nfe": register.tp_nfe,
                "serie_nota": register.serie_nota,
                "id_pedido": register.id_pedido,
                "id_cliente": register.id_cliente,
                "nome_cliente": register.nome_cliente,
                "vendedor_pedido": register.vendedor_pedido,
                "vendedor_pedido_id": register.vendedor_pedido_id,
                "valor_total_produtos": register.valor_total_produtos,
                "desconto_pedido": register.desconto_pedido,
                "peso_total_nota": register.peso_total_nota,
                "peso_total_nota_liq": register.peso_total_nota_liq,
                "frete_pedido": register.frete_pedido,
                "valor_total_nota": register.valor_total_nota,
                "valor_baseICMS": register.valor_baseICMS,
                "valor_ICMS": register.valor_ICMS,
                "valor_baseST": register.valor_baseST,
                "valor_ST": register.valor_ST,
                "valor_IPI": register.valor_IPI,
                "valor_despesas": register.valor_despesas,
                "condicao_pagamento": register.condicao_pagamento,
                "transportadora_pedido": register.transportadora_pedido,
                "id_transportadora": register.id_transportadora,
                "frete_por_pedido": register.frete_por_pedido,
                "volumes_transporta": register.volumes_transporta,
                "especie_transporta": register.especie_transporta,
                "marca_transporta": register.marca_transporta,
                "numeracao_transporta": register.numeracao_transporta,
                "placa_transporta": register.placa_transporta,
                "uf_embarque": register.uf_embarque,
                "local_embarque": register.local_embarque,
                "data_pedido": register.data_pedido,
                "data_pedido_hora": register.data_pedido_hora,
                "data_emissao": register.data_emissao,
                "natureza_pedido": register.natureza_pedido,
                "finalidade_nfe": register.finalidade_nfe,
                "obs_pedido": register.obs_pedido,
                "obs_interno_pedido": register.obs_interno_pedido,
                "status_pedido": register.status_pedido,
                "contas_pedido": register.contas_pedido,
                "comissao_pedido": register.comissao_pedido,
                "boletos_pedido": register.boletos_pedido,
                "estoque_pedido": register.estoque_pedido,
                "nota_emitida": register.nota_emitida,
                "nota_chave": register.nota_chave,
                "nota_protocolo": register.nota_protocolo,
                "nota_codigov": register.nota_codigov,
                "nota_recibo": register.nota_recibo,
                "nota_data_autorizacao": register.nota_data_autorizacao,
                "nota_usuario_autorizacao": register.nota_usuario_autorizacao,
                "nota_data_cancelamento": register.nota_data_cancelamento,
                "nota_usuario_cancelamento": register.nota_usuario_cancelamento,
                "nota_motivo_cancelamento": register.nota_motivo_cancelamento,
                "nota_denegada": register.nota_denegada,
                "nota_importada": register.nota_importada,
                "nota_scan": register.nota_scan,
                "data_cad_pedido": register.data_cad_pedido,
                "data_mod_pedido": register.data_mod_pedido,
                "ambiente": register.ambiente,
                "lixeira": register.lixeira,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_venda",
            "tp_nfe",
            "serie_nota",
            "id_pedido",
            "id_cliente",
            "nome_cliente",
            "vendedor_pedido",
            "vendedor_pedido_id",
            "valor_total_produtos",
            "desconto_pedido",
            "peso_total_nota",
            "peso_total_nota_liq",
            "frete_pedido",
            "valor_total_nota",
            "valor_baseICMS",
            "valor_ICMS",
            "valor_baseST",
            "valor_ST",
            "valor_IPI",
            "valor_despesas",
            "condicao_pagamento",
            "transportadora_pedido",
            "id_transportadora",
            "frete_por_pedido",
            "volumes_transporta",
            "especie_transporta",
            "marca_transporta",
            "numeracao_transporta",
            "placa_transporta",
            "uf_embarque",
            "local_embarque",
            "data_pedido",
            "data_pedido_hora",
            "data_emissao",
            "natureza_pedido",
            "finalidade_nfe",
            "obs_pedido",
            "obs_interno_pedido",
            "status_pedido",
            "contas_pedido",
            "comissao_pedido",
            "boletos_pedido",
            "estoque_pedido",
            "nota_emitida",
            "nota_chave",
            "nota_protocolo",
            "nota_codigov",
            "nota_recibo",
            "nota_data_autorizacao",
            "nota_usuario_autorizacao",
            "nota_data_cancelamento",
            "nota_usuario_cancelamento",
            "nota_motivo_cancelamento",
            "nota_importada",
            "nota_scan",
            "data_cad_pedido",
            "data_mod_pedido",
            "ambiente",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "serie_nota")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        create_nf(group[0])
                        print("Create")
                    except Exception as e:
                        print(f"An error occurred: {e}")
            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:

                        print("Update")
                    except Exception as e:
                        print(f"An error occurred: {e}")
        return {
            "message": "NF updates have been processed.",
            "API elements": self.api_elements,
        }
