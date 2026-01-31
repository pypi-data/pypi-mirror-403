import unittest

from gou2tool.util.company_util import CompanyUtil


class TestDemo(unittest.TestCase):
    def test_name(self):
        company_list = [
            "台山市台城向日葵美业工作室（个体工商户）",
            "北京美宸伟业住房租赁有限责任公司",
            "大连美林达企业管理咨询有限公司",
            "佛山美林达企业管理咨询有限公司",
            "上海美林达企业管理咨询有限公司",
            "海口诺美施企业管理有限公司",
            "经开区悦己美业店（个体工商户）",
            "昆明倾诚悦秀美业品牌管理有限公司第一分公司",
            "青岛澜绮美业科技有限公司",
            "上海白钥美品农业发展有限公司",
            "宁波市鄞州中河美丁酒业商行（个体工商户）",
        ]
        for company in company_list:
            print(CompanyUtil.name(company), "=>", company)
        self.assertTrue(True)

    def test_is_code(self):
        code_list = [
            "02050024-8",
            "02050033-6",
            "1022200060",
            "17784281-X",
            "17179539",
            "18395151",
            "1101091484294",
            "4100001005849",
            "410102600122284",
            "410102600185624",
            "410102600226005",
            "410102600251434",
            "52411002MJG3817371",
            "52410902MJY840158K",
            "52420100MJH27161X9",
            "52420105MJH327396Q",
            "52421381MJJ0681139",
            "52430302MJJ54313XF",
            "92420103MA4EH5150N",
            "81430424MCA2883098",
            "91110101MA01RY9F8D",
            "91110106MAK31Y5B6M",
            "91110108082808205D",
            "92420111MAC2WJBX76",
            "92410781MADD2N620M",
            "91110109MA007J269E",
            "92429004MADCTPM672",
            "92410902MA45PCQ03X",
            "92411303MAE5D30Y43",
            "91430124MA4Q9N3N7L",
            "92420113MA4JAW9P50",
            "92410100MADWJHEM9P",
            "92410303MA9HUDW1XR",
        ]
        for code in code_list:
            print(CompanyUtil.is_code(code), "=>", code)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
