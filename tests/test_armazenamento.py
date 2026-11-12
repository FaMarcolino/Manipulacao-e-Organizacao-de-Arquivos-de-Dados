"""Testes unitários (python -m unittest discover -s tests -v, a partir da raiz)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import armazenamento as arm  # noqa: E402
import estatisticas as est  # noqa: E402
from gerador import gerar_alunos  # noqa: E402
from registro import (  # noqa: E402
    TAMANHO_FIXO, desserializar_fixo, desserializar_variavel,
    serializar_fixo, serializar_variavel,
)


class TestRegistro(unittest.TestCase):
    def test_tamanho_fixo_maximo(self):
        self.assertEqual(TAMANHO_FIXO, 169)

    def test_todos_registros_fixos_tem_mesmo_tamanho(self):
        for a in gerar_alunos(200):
            self.assertEqual(len(serializar_fixo(a)), TAMANHO_FIXO)

    def test_ida_e_volta(self):
        for a in gerar_alunos(200):
            self.assertEqual(desserializar_fixo(serializar_fixo(a)), a)
            self.assertEqual(desserializar_variavel(serializar_variavel(a)), a)

    def test_variavel_em_media_menor_que_fixo(self):
        alunos = gerar_alunos(200)
        media = sum(len(serializar_variavel(a)) + arm.TAM_CABECALHO for a in alunos) / len(alunos)
        self.assertLess(media, TAMANHO_FIXO)

    def test_matriculas_unicas(self):
        alunos = gerar_alunos(2000)
        self.assertEqual(len({a.matricula for a in alunos}), 2000)


class TestEmpacotamento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alunos = gerar_alunos(500)

    def _ida_e_volta(self, modo, tam_bloco):
        blocos = arm.empacotar(modo, self.alunos, tam_bloco)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "t.dat")
            arm.gravar(blocos, tam_bloco, caminho)
            self.assertEqual(os.path.getsize(caminho), len(blocos) * tam_bloco)
            self.assertEqual(arm.ler(caminho, tam_bloco, modo), self.alunos)
        return blocos

    def test_nenhum_bloco_excede_limite(self):
        for modo in arm.MODOS:
            for tam in (256, 300, 512, 1000, 4096):
                for b in arm.empacotar(modo, self.alunos, tam):
                    self.assertLessEqual(b.ocupados, tam)

    def test_ida_e_volta_todos_os_modos(self):
        for modo in arm.MODOS:
            for tam in (200, 256, 512, 777, 4096):
                with self.subTest(modo=modo, bloco=tam):
                    self._ida_e_volta(modo, tam)

    def test_espalhado_com_blocos_minusculos(self):
        # Bloco de 4 bytes = cabeçalho + 1 byte de dado: caso extremo.
        alunos = gerar_alunos(5)
        blocos = arm.empacotar_variavel_espalhado(alunos, 4)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "t.dat")
            arm.gravar(blocos, 4, caminho)
            self.assertEqual(arm.ler(caminho, 4, arm.VARIAVEL_ESPALHADO), alunos)

    def test_fixo_registros_por_bloco(self):
        blocos = arm.empacotar_fixo(self.alunos, 512)  # 512 // 169 = 3
        self.assertEqual(len(blocos), -(-500 // 3))
        self.assertTrue(all(b.ocupados == 3 * TAMANHO_FIXO for b in blocos[:-1]))

    def test_fixo_nao_cruza_bloco(self):
        for b in arm.empacotar_fixo(self.alunos, 400):
            self.assertEqual(b.ocupados % TAMANHO_FIXO, 0)

    def test_contiguo_nao_fragmenta(self):
        blocos = arm.empacotar_variavel_contiguo(self.alunos, 512)
        self.assertFalse(any(b.herda_fragmento or b.deixa_fragmento for b in blocos))

    def test_espalhado_usa_menos_ou_igual_blocos_que_contiguo(self):
        for tam in (256, 512, 1024):
            c = len(arm.empacotar_variavel_contiguo(self.alunos, tam))
            e = len(arm.empacotar_variavel_espalhado(self.alunos, tam))
            self.assertLessEqual(e, c)

    def test_espalhado_enche_blocos(self):
        blocos = arm.empacotar_variavel_espalhado(self.alunos, 512)
        # Só pode sobrar espaço (< 4 bytes) antes de abrir novo bloco.
        for b in blocos[:-1]:
            self.assertGreaterEqual(b.ocupados, 512 - (arm.TAM_CABECALHO))

    def test_erro_bloco_pequeno(self):
        with self.assertRaises(arm.ErroArmazenamento):
            arm.empacotar_fixo(self.alunos, 168)
        with self.assertRaises(arm.ErroArmazenamento):
            arm.empacotar_variavel_contiguo(self.alunos, 100)
        with self.assertRaises(arm.ErroArmazenamento):
            arm.empacotar_variavel_espalhado(self.alunos, 3)


class TestEstatisticas(unittest.TestCase):
    def test_exemplo_do_enunciado(self):
        # Blocos de 512 bytes com 512, 486 e 210 bytes => 78,6% (1208/1536).
        blocos = []
        for ocupados in (512, 486, 210):
            b = arm.Bloco()
            b.dados = bytearray(ocupados)
            b.uteis = ocupados
            blocos.append(b)
        e = est.calcular(blocos, 512, 10)
        self.assertEqual(e.total_blocos, 3)
        self.assertEqual(e.blocos_cheios, 1)
        self.assertEqual(e.blocos_parciais, 2)
        self.assertEqual(est.pct(e.eficiencia), "78,6%")

    def test_uteis_nunca_excedem_ocupados(self):
        alunos = gerar_alunos(300)
        for modo in arm.MODOS:
            for b in arm.empacotar(modo, alunos, 512):
                self.assertLessEqual(b.uteis, b.ocupados)

    def test_uteis_totais_iguais_em_todos_os_modos(self):
        alunos = gerar_alunos(300)
        totais = {m: sum(b.uteis for b in arm.empacotar(m, alunos, 512)) for m in arm.MODOS}
        self.assertEqual(len(set(totais.values())), 1)


if __name__ == "__main__":
    unittest.main()
