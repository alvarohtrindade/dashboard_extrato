from typing import Optional, List, Tuple
from .models import FilterParams

class QueryBuilder:
    """Construtor de queries SQL para diferentes análises"""
    
    def build_extract_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query principal para dados de extrato"""
        base_query = """
        SELECT 
            id_origem,
            fonte,
            id_carteira,
            nmfundo,
            cnpj,
            dt_lancamento,
            COALESCE(entrada, 0) as entrada,
            COALESCE(saida, 0) as saida,
            COALESCE(saldo, 0) as saldo,
            lancamento
        FROM DW_STAGING.vw_extrato
        WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        ORDER BY dt_lancamento DESC, nmfundo
        """
        
        if filters.limit:
            base_query += f" LIMIT {filters.limit}"
        
        return base_query, tuple(params)
    
    def build_liquidity_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query para métricas de liquidez"""
        base_query = """
        SELECT 
            nmfundo,
            fonte,
            SUM(COALESCE(entrada, 0)) as total_entries,
            SUM(COALESCE(saida, 0)) as total_exits,
            SUM(COALESCE(entrada, 0) - COALESCE(saida, 0)) as net_flow,
            COUNT(*) as operation_count,
            COUNT(DISTINCT DATE(dt_lancamento)) as active_days,
            AVG(COALESCE(entrada, 0) - COALESCE(saida, 0)) as avg_daily_flow,
            STDDEV(COALESCE(entrada, 0) - COALESCE(saida, 0)) as flow_volatility,
            MAX(ABS(COALESCE(entrada, 0) - COALESCE(saida, 0))) as max_daily_flow,
            MIN(COALESCE(saldo, 0)) as min_balance,
            MAX(COALESCE(saldo, 0)) as max_balance
        FROM DW_STAGING.vw_extrato
        WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        GROUP BY nmfundo, fonte
        HAVING SUM(ABS(COALESCE(entrada, 0)) + ABS(COALESCE(saida, 0))) > 0
        ORDER BY total_entries + total_exits DESC
        """
        
        return base_query, tuple(params)
    
    def build_daily_metrics_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query para métricas diárias"""
        base_query = """
        SELECT 
            DATE(dt_lancamento) as date,
            nmfundo,
            fonte,
            SUM(COALESCE(entrada, 0)) as daily_entries,
            SUM(COALESCE(saida, 0)) as daily_exits,
            SUM(COALESCE(entrada, 0) - COALESCE(saida, 0)) as daily_net_flow,
            COUNT(*) as daily_operations,
            AVG(COALESCE(saldo, 0)) as avg_balance,
            MAX(COALESCE(saldo, 0)) as max_balance,
            MIN(COALESCE(saldo, 0)) as min_balance
        FROM DW_STAGING.vw_extrato
        WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        GROUP BY DATE(dt_lancamento), nmfundo, fonte
        ORDER BY date DESC, nmfundo
        """
        
        return base_query, tuple(params)
    
    def build_concentration_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query para análise de concentração"""
        base_query = """
        WITH fund_totals AS (
            SELECT 
                nmfundo,
                fonte,
                SUM(ABS(COALESCE(entrada, 0)) + ABS(COALESCE(saida, 0))) as total_volume,
                COUNT(*) as operation_count
            FROM DW_STAGING.vw_extrato
            WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
            GROUP BY nmfundo, fonte
        ),
        overall_total AS (
            SELECT SUM(total_volume) as grand_total
            FROM fund_totals
        )
        SELECT 
            f.nmfundo,
            f.fonte,
            f.total_volume,
            f.operation_count,
            ROUND((f.total_volume / o.grand_total) * 100, 2) as concentration_pct,
            CASE 
                WHEN (f.total_volume / o.grand_total) * 100 > 30 THEN 'Alto'
                WHEN (f.total_volume / o.grand_total) * 100 > 20 THEN 'Médio'
                ELSE 'Baixo'
            END as concentration_level
        FROM fund_totals f
        CROSS JOIN overall_total o
        WHERE f.total_volume > 0
        ORDER BY concentration_pct DESC
        """
        
        return base_query, tuple(params)
    
    def build_balance_evolution_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query para evolução do saldo"""
        base_query = """
        SELECT 
            DATE(dt_lancamento) as date,
            nmfundo,
            fonte,
            COALESCE(entrada, 0) - COALESCE(saida, 0) as daily_change,
            COALESCE(saldo, 0) as balance,
            LAG(COALESCE(saldo, 0)) OVER (
                PARTITION BY nmfundo ORDER BY dt_lancamento
            ) as previous_balance
        FROM DW_STAGING.vw_extrato
        WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        ORDER BY dt_lancamento, nmfundo
        """
        
        return base_query, tuple(params)
    
    def build_operation_summary_query(self, filters: FilterParams) -> Tuple[str, Tuple]:
        """Query para resumo de operações por categoria"""
        base_query = """
        SELECT 
            CASE 
                WHEN LOWER(lancamento) LIKE '%taxa%' OR LOWER(lancamento) LIKE '%fee%' THEN 'Taxa'
                WHEN LOWER(lancamento) LIKE '%aplic%' OR LOWER(lancamento) LIKE '%aporte%' THEN 'Aplicação'
                WHEN LOWER(lancamento) LIKE '%resgate%' OR LOWER(lancamento) LIKE '%saque%' THEN 'Resgate'
                WHEN LOWER(lancamento) LIKE '%rendimento%' OR LOWER(lancamento) LIKE '%juros%' THEN 'Rendimento'
                WHEN LOWER(lancamento) LIKE '%compra%' THEN 'Compra'
                WHEN LOWER(lancamento) LIKE '%venda%' THEN 'Venda'
                ELSE 'Outros'
            END as categoria,
            COUNT(*) as total_operations,
            SUM(COALESCE(entrada, 0)) as total_entries,
            SUM(COALESCE(saida, 0)) as total_exits,
            SUM(COALESCE(entrada, 0) - COALESCE(saida, 0)) as net_amount,
            COUNT(DISTINCT nmfundo) as affected_funds,
            AVG(ABS(COALESCE(entrada, 0) - COALESCE(saida, 0))) as avg_operation_size
        FROM DW_STAGING.vw_extrato
        WHERE DATE(dt_lancamento) BETWEEN %s AND %s
        """
        
        params = [filters.start_date, filters.end_date]
        conditions = []
        
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            conditions.append(f"nmfundo IN ({fund_placeholders})")
            params.extend(filters.funds)
        
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            conditions.append(f"fonte IN ({custodian_placeholders})")
            params.extend(filters.custodians)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        GROUP BY categoria
        HAVING total_operations > 0
        ORDER BY ABS(net_amount) DESC
        """
        
        return base_query, tuple(params)