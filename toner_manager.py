#!/usr/bin/env python3
"""Sistema de gestão de toners, cilindros e impressoras por departamento."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DB = Path("toner_manager.db")


@dataclass
class EstoqueItem:
    id: int
    nome: str
    estoque_atual: int


class TonerManager:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS toner_model (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    estoque_atual INTEGER NOT NULL DEFAULT 0 CHECK (estoque_atual >= 0)
                );

                CREATE TABLE IF NOT EXISTS cilindro_model (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    estoque_atual INTEGER NOT NULL DEFAULT 0 CHECK (estoque_atual >= 0)
                );

                CREATE TABLE IF NOT EXISTS departamento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS impressora (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patrimonio TEXT NOT NULL UNIQUE,
                    modelo TEXT NOT NULL,
                    departamento_id INTEGER NOT NULL,
                    toner_model_id INTEGER NOT NULL,
                    cilindro_model_id INTEGER NOT NULL,
                    FOREIGN KEY (departamento_id) REFERENCES departamento(id) ON DELETE RESTRICT,
                    FOREIGN KEY (toner_model_id) REFERENCES toner_model(id) ON DELETE RESTRICT,
                    FOREIGN KEY (cilindro_model_id) REFERENCES cilindro_model(id) ON DELETE RESTRICT
                );
                """
            )

    def add_toner_model(self, nome: str, estoque_inicial: int = 0) -> None:
        self._validate_non_negative(estoque_inicial)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO toner_model (nome, estoque_atual) VALUES (?, ?)",
                (nome.strip(), estoque_inicial),
            )

    def add_cilindro_model(self, nome: str, estoque_inicial: int = 0) -> None:
        self._validate_non_negative(estoque_inicial)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cilindro_model (nome, estoque_atual) VALUES (?, ?)",
                (nome.strip(), estoque_inicial),
            )

    def add_departamento(self, nome: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO departamento (nome) VALUES (?)", (nome.strip(),))

    def add_impressora(
        self,
        patrimonio: str,
        modelo: str,
        departamento_id: int,
        toner_model_id: int,
        cilindro_model_id: int,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO impressora (
                    patrimonio, modelo, departamento_id, toner_model_id, cilindro_model_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (patrimonio.strip(), modelo.strip(), departamento_id, toner_model_id, cilindro_model_id),
            )

    def movimentar_estoque(self, tipo: str, model_id: int, delta: int) -> None:
        tabela = self._resolve_tipo_tabela(tipo)
        with self._connect() as conn:
            cur = conn.execute(f"SELECT estoque_atual FROM {tabela} WHERE id = ?", (model_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Modelo id={model_id} não encontrado em {tipo}")
            novo_estoque = row["estoque_atual"] + delta
            if novo_estoque < 0:
                raise ValueError("Movimentação inválida: estoque não pode ficar negativo")
            conn.execute(f"UPDATE {tabela} SET estoque_atual = ? WHERE id = ?", (novo_estoque, model_id))

    def listar_estoque(self, tipo: str) -> list[EstoqueItem]:
        tabela = self._resolve_tipo_tabela(tipo)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT id, nome, estoque_atual FROM {tabela} ORDER BY nome ASC"
            ).fetchall()
            return [EstoqueItem(r["id"], r["nome"], r["estoque_atual"]) for r in rows]

    def listar_impressoras(self) -> Iterable[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT
                    i.id,
                    i.patrimonio,
                    i.modelo,
                    d.nome AS departamento,
                    t.nome AS toner,
                    c.nome AS cilindro
                FROM impressora i
                JOIN departamento d ON d.id = i.departamento_id
                JOIN toner_model t ON t.id = i.toner_model_id
                JOIN cilindro_model c ON c.id = i.cilindro_model_id
                ORDER BY d.nome, i.patrimonio
                """
            ).fetchall()

    @staticmethod
    def _resolve_tipo_tabela(tipo: str) -> str:
        key = tipo.strip().lower()
        if key == "toner":
            return "toner_model"
        if key == "cilindro":
            return "cilindro_model"
        raise ValueError("Tipo deve ser 'toner' ou 'cilindro'")

    @staticmethod
    def _validate_non_negative(value: int) -> None:
        if value < 0:
            raise ValueError("Valor não pode ser negativo")


def print_estoque(items: list[EstoqueItem], titulo: str) -> None:
    print(f"\n{titulo}")
    print("-" * len(titulo))
    if not items:
        print("Nenhum item cadastrado.")
        return

    for item in items:
        print(f"[{item.id}] {item.nome}: {item.estoque_atual}")


def print_impressoras(rows: Iterable[sqlite3.Row]) -> None:
    rows = list(rows)
    print("\nImpressoras cadastradas")
    print("----------------------")
    if not rows:
        print("Nenhuma impressora cadastrada.")
        return
    for row in rows:
        print(
            f"[{row['id']}] Patrimônio: {row['patrimonio']} | Modelo: {row['modelo']} | "
            f"Departamento: {row['departamento']} | Toner: {row['toner']} | Cilindro: {row['cilindro']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestão de toners/cilindros e impressoras")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Caminho do banco SQLite")
    sub = parser.add_subparsers(dest="command", required=True)

    add_toner = sub.add_parser("add-toner", help="Cadastrar modelo de toner")
    add_toner.add_argument("nome")
    add_toner.add_argument("--estoque", type=int, default=0)

    add_cil = sub.add_parser("add-cilindro", help="Cadastrar modelo de cilindro")
    add_cil.add_argument("nome")
    add_cil.add_argument("--estoque", type=int, default=0)

    add_dep = sub.add_parser("add-departamento", help="Cadastrar departamento")
    add_dep.add_argument("nome")

    add_imp = sub.add_parser("add-impressora", help="Cadastrar impressora")
    add_imp.add_argument("patrimonio")
    add_imp.add_argument("modelo")
    add_imp.add_argument("departamento_id", type=int)
    add_imp.add_argument("toner_model_id", type=int)
    add_imp.add_argument("cilindro_model_id", type=int)

    mov = sub.add_parser("movimentar", help="Movimentar estoque")
    mov.add_argument("tipo", choices=["toner", "cilindro"])
    mov.add_argument("model_id", type=int)
    mov.add_argument("delta", type=int, help="Valor positivo (entrada) ou negativo (saída)")

    list_est = sub.add_parser("estoque", help="Listar estoque")
    list_est.add_argument("tipo", choices=["toner", "cilindro"])

    sub.add_parser("impressoras", help="Listar impressoras")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    manager = TonerManager(args.db)

    try:
        if args.command == "add-toner":
            manager.add_toner_model(args.nome, args.estoque)
            print("Modelo de toner cadastrado com sucesso.")
        elif args.command == "add-cilindro":
            manager.add_cilindro_model(args.nome, args.estoque)
            print("Modelo de cilindro cadastrado com sucesso.")
        elif args.command == "add-departamento":
            manager.add_departamento(args.nome)
            print("Departamento cadastrado com sucesso.")
        elif args.command == "add-impressora":
            manager.add_impressora(
                args.patrimonio,
                args.modelo,
                args.departamento_id,
                args.toner_model_id,
                args.cilindro_model_id,
            )
            print("Impressora cadastrada com sucesso.")
        elif args.command == "movimentar":
            manager.movimentar_estoque(args.tipo, args.model_id, args.delta)
            print("Estoque atualizado com sucesso.")
        elif args.command == "estoque":
            itens = manager.listar_estoque(args.tipo)
            titulo = "Estoque de toner" if args.tipo == "toner" else "Estoque de cilindro"
            print_estoque(itens, titulo)
        elif args.command == "impressoras":
            print_impressoras(manager.listar_impressoras())
    except (sqlite3.IntegrityError, ValueError) as exc:
        print(f"Erro: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
