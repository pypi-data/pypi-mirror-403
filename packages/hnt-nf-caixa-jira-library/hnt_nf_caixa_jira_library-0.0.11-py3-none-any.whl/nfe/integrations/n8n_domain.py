import json
import requests
from ..HntException import HntException
from ..constants import API_DOMAIN_N8N_URL, API_HEADERS, N8N_AUTH
from ..model.n8n_domain_model import FornecedorCaixa, FornecedorMaterial
class N8NDomain:
    def post_tbl_hnt_nf_access_key_jira_control(self, data: dict):
        payload = json.dumps(data)
        res = requests.post(            
            f"{API_DOMAIN_N8N_URL}/474e77cb-48f5-4949-af7b-97573cc2c98e/hnt/tbl_hnt_nf_access_key_jira_control/domain",
            auth=N8N_AUTH,
            headers=API_HEADERS,
            data=payload)
        res.raise_for_status()
        return res.json()
    def get_sefax_xml(self, cnpj_destinatario, chave_acesso, issue_key):
        if cnpj_destinatario is None or chave_acesso is None or issue_key is None:
            raise HntException('')
        url = f"{API_DOMAIN_N8N_URL}/hnt/sefaz/xml?cnpj_destinatario={cnpj_destinatario}&chave_acesso={chave_acesso}&issue_key={issue_key}"
        n8n_data = self._get_nf_domain_response(url)
        return n8n_data

    def get_fornecedor_caixa(self, nro_documento):
        url = f"{API_DOMAIN_N8N_URL}/hnt/fornecedor_caixa?nro_documento={nro_documento}"
        n8n_domain_response = self._get_nf_domain_response(url)
        # Validar se há conteúdo antes de parsear JSON
        if not n8n_domain_response.text or not n8n_domain_response.content:
            raise HntException(f"Não encontramos o fornecedor informado. Verifique o número do documento ({nro_documento}) do fornecedor e tente novamente.")
        
        domain_data = n8n_domain_response.json()

        if not domain_data:
            raise HntException(f"Could not find domain, url: {url}")
        if len(domain_data) == 0:
            raise HntException(f"Could not find FornecedorCaixa, nro_documento: {nro_documento}")
        model = []
        for item in domain_data:
            model.append(FornecedorCaixa.model_validate(item))
        return model

    def get_fornecedor_material(self, nro_documento, cod_material_fornecedor):
        url = f"{API_DOMAIN_N8N_URL}/hnt/fornecedor_material?nro_documento_fornecedor={nro_documento}&cod_material_fornecedor={cod_material_fornecedor}"
        n8n_domain_response = self._get_nf_domain_response(url)
        n8n_domain_data = n8n_domain_response.json()
        # if API returns a success flag, consider absence when it's falsy
        if 'success' in n8n_domain_data and n8n_domain_data.get('success'):
            error_msg = f"Não foi possível localizar o material do fornecedor para o nº do documento {nro_documento} e o código do material do fornecedor {cod_material_fornecedor}."
            raise HntException(error_msg)
        return FornecedorMaterial.model_validate(n8n_domain_data)

    def _get_nf_domain_response(self, url):
        try:
            domain_res = requests.get(
                url,
                auth=N8N_AUTH,
            )
            domain_res.raise_for_status()
            return domain_res
        except Exception as e:
            raise HntException("Erro ao receber dados do domínio n8n", cause=e)

