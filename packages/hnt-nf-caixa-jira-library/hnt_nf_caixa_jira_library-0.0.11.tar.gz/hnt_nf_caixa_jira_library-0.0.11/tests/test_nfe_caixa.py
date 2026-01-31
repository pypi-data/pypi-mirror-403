import json
from nfe.HntException import HntException
from nfe.nfe_caixa import NFeCaixa
class TestNFeCaixa:
    def setup_method(self, method):
        with open(f"./devdata/json/{method.__name__}.json", "r", encoding="utf-8") as arquivo_json: nfe = json.load(arquivo_json)
        self.nfe = nfe
        self.nfe_caixa = None

    def test_cnpj_37969285000183(self):
        self.nfe_caixa = NFeCaixa().build('GHN-78430', self.nfe)

    def test_many_fornecedores_cfp_15861804877(self):
        try:
            self.nfe_caixa = NFeCaixa().build('GHN-79390', self.nfe)
            assert False, "Expected HntException was not raised"
        except HntException as e:
            assert str(e) == "HNTException: Não encontramos o fornecedor informado. Verifique o número do documento (15861804877) do fornecedor e tente novamente."

    def test_not_found_material_cfp_15861804877(self):
        try:
            self.nfe_caixa = NFeCaixa().build('GHN-69904', self.nfe)
            assert False, "Expected HntException was not raised"
        except HntException as e:
            assert str(e) == "HNTException: Não foi possível localizar o material do fornecedor para o nº do documento 15861804877 e o código do material do fornecedor 559133."


    def teardown_method(self, method):
        if self.nfe_caixa is not None:
            with open(f"./output/json/{method.__name__}.json", "w", encoding="utf-8") as json_file:
                json.dump(self.nfe_caixa.model_dump(mode="json"), json_file, ensure_ascii=False, indent=4, default=str)

