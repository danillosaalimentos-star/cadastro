import tempfile
import unittest
from pathlib import Path

from toner_manager import TonerManager


class TonerManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        self.manager = TonerManager(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_fluxo_basico(self):
        self.manager.add_toner_model("HP 58A", 10)
        self.manager.add_cilindro_model("DR-1060", 5)
        self.manager.add_departamento("TI")
        self.manager.add_impressora("IMP-10", "Brother 5102", 1, 1, 1)

        toners = self.manager.listar_estoque("toner")
        cilindros = self.manager.listar_estoque("cilindro")
        impressoras = list(self.manager.listar_impressoras())

        self.assertEqual(1, len(toners))
        self.assertEqual(10, toners[0].estoque_atual)
        self.assertEqual(1, len(cilindros))
        self.assertEqual("TI", impressoras[0]["departamento"])

    def test_movimentacao_estoque(self):
        self.manager.add_toner_model("HP 58A", 2)
        self.manager.movimentar_estoque("toner", 1, 3)
        self.manager.movimentar_estoque("toner", 1, -1)
        toners = self.manager.listar_estoque("toner")
        self.assertEqual(4, toners[0].estoque_atual)

    def test_nao_permite_estoque_negativo(self):
        self.manager.add_cilindro_model("DR-1060", 1)
        with self.assertRaises(ValueError):
            self.manager.movimentar_estoque("cilindro", 1, -2)


if __name__ == "__main__":
    unittest.main()
