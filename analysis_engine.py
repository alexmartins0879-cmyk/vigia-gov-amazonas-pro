"""
Motor de análise com 7 regras de alerta automáticas
"""
import logging
from statistics import mean, median, stdev, quantiles
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Motor de análise de contratos com regras de alerta"""
    
    # 7 Regras de Alerta
    ALERT_RULES = {
        1: "Fornecedor Único",
        2: "Valor Muito Acima da Média",
        3: "Valor Muito Abaixo da Média",
        4: "Descrição Genérica",
        5: "Contratação Direta sem Justificativa",
        6: "Repetição de Fornecedores",
        7: "Valores Suspeitos por Setor"
    }
    
    RISK_LEVELS = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴"
    }
    
    def __init__(self):
        self.alerts = []
    
    def analisar_contratos(self, contratos: List[Dict]) -> Dict:
        """
        Analisa lista de contratos e aplica todas as regras
        
        Args:
            contratos: Lista de contratos
            
        Returns:
            Dicionário com análise completa
        """
        if not contratos:
            return {"alertas": [], "estatisticas": {}, "resumo": {}}
        
        self.alerts = []
        
        # Aplicar cada regra
        self._regra_1_fornecedor_unico(contratos)
        self._regra_2_valor_acima_media(contratos)
        self._regra_3_valor_abaixo_media(contratos)
        self._regra_4_descricao_generica(contratos)
        self._regra_5_contratacao_direta(contratos)
        self._regra_6_repeticion_fornecedores(contratos)
        self._regra_7_valores_suspeitos(contratos)
        
        # Gerar estatísticas
        stats = self._gerar_estatisticas(contratos)
        
        # Gerar resumo de risco
        resumo = self._gerar_resumo_risco(contratos)
        
        return {
            "alertas": self.alerts,
            "estatisticas": stats,
            "resumo": resumo,
            "total_contratos": len(contratos),
            "total_alertas": len(self.alerts)
        }
    
    def _regra_1_fornecedor_unico(self, contratos: List[Dict]):
        """Regra 1: Fornecedor Único - um fornecedor ganha quase todos os contratos"""
        fornecedores = {}
        
        for contrato in contratos:
            cnpj = contrato.get('cnpj_fornecedor', '')
            fornecedores[cnpj] = fornecedores.get(cnpj, 0) + 1
        
        total = len(contratos)
        threshold = total * 0.7  # 70% dos contratos
        
        for cnpj, count in fornecedores.items():
            if count >= threshold:
                self.alerts.append({
                    "regra": 1,
                    "tipo": self.ALERT_RULES[1],
                    "cnpj_fornecedor": cnpj,
                    "descricao": f"Fornecedor venceu {count} de {total} contratos ({(count/total)*100:.1f}%)",
                    "risco": "HIGH",
                    "icon": self.RISK_LEVELS["HIGH"]
                })
    
    def _regra_2_valor_acima_media(self, contratos: List[Dict]):
        """Regra 2: Valor muito acima da média (outlier superior)"""
        valores = [c.get('valor_contratado', 0) for c in contratos if c.get('valor_contratado')]
        
        if len(valores) < 2:
            return
        
        try:
            media = mean(valores)
            desvio = stdev(valores)
            threshold = media + (2 * desvio)  # 2 desvios padrão acima
            
            for contrato in contratos:
                valor = contrato.get('valor_contratado', 0)
                if valor > threshold:
                    diferenca = valor - media
                    self.alerts.append({
                        "regra": 2,
                        "tipo": self.ALERT_RULES[2],
                        "numero_processo": contrato.get('numero_processo'),
                        "valor": valor,
                        "valor_medio": media,
                        "diferenca": diferenca,
                        "descricao": f"Valor R$ {valor:,.2f} está R$ {diferenca:,.2f} acima da média",
                        "risco": "MEDIUM",
                        "icon": self.RISK_LEVELS["MEDIUM"]
                    })
        except Exception as e:
            logger.error(f"Erro na regra 2: {e}")
    
    def _regra_3_valor_abaixo_media(self, contratos: List[Dict]):
        """Regra 3: Valor muito abaixo da média (pode indicar subcontratação)"""
        valores = [c.get('valor_contratado', 0) for c in contratos if c.get('valor_contratado')]
        
        if len(valores) < 2:
            return
        
        try:
            media = mean(valores)
            desvio = stdev(valores)
            threshold = media - (2 * desvio)  # 2 desvios padrão abaixo
            
            for contrato in contratos:
                valor = contrato.get('valor_contratado', 0)
                if 0 < valor < threshold:
                    diferenca = media - valor
                    self.alerts.append({
                        "regra": 3,
                        "tipo": self.ALERT_RULES[3],
                        "numero_processo": contrato.get('numero_processo'),
                        "valor": valor,
                        "valor_medio": media,
                        "diferenca": diferenca,
                        "descricao": f"Valor R$ {valor:,.2f} está R$ {diferenca:,.2f} abaixo da média",
                        "risco": "LOW",
                        "icon": self.RISK_LEVELS["LOW"]
                    })
        except Exception as e:
            logger.error(f"Erro na regra 3: {e}")
    
    def _regra_4_descricao_generica(self, contratos: List[Dict]):
        """Regra 4: Descrição genérica (pode indicar direcionamento)"""
        genericas = ["serviços", "materiais", "diversos", "geral", "não especificado"]
        
        for contrato in contratos:
            descricao = (contrato.get('descricao_objeto', '') or '').lower()
            
            if any(gen in descricao for gen in genericas) and len(descricao) < 50:
                self.alerts.append({
                    "regra": 4,
                    "tipo": self.ALERT_RULES[4],
                    "numero_processo": contrato.get('numero_processo'),
                    "descricao": f"Descrição muito genérica: '{descricao}'",
                    "risco": "MEDIUM",
                    "icon": self.RISK_LEVELS["MEDIUM"]
                })
    
    def _regra_5_contratacao_direta(self, contratos: List[Dict]):
        """Regra 5: Contratação direta sem justificativa clara"""
        for contrato in contratos:
            tipo = (contrato.get('tipo_contratacao', '') or '').lower()
            justificativa = (contrato.get('justificativa', '') or '').strip()
            
            if 'direta' in tipo and (not justificativa or len(justificativa) < 20):
                self.alerts.append({
                    "regra": 5,
                    "tipo": self.ALERT_RULES[5],
                    "numero_processo": contrato.get('numero_processo'),
                    "tipo_contratacao": contrato.get('tipo_contratacao'),
                    "descricao": "Contratação direta sem justificativa suficiente",
                    "risco": "HIGH",
                    "icon": self.RISK_LEVELS["HIGH"]
                })
    
    def _regra_6_repeticion_fornecedores(self, contratos: List[Dict]):
        """Regra 6: Repetição excessiva de fornecedores"""
        fornecedores = {}
        
        for contrato in contratos:
            cnpj = contrato.get('cnpj_fornecedor', '')
            if cnpj not in fornecedores:
                fornecedores[cnpj] = []
            fornecedores[cnpj].append(contrato.get('numero_processo'))
        
        for cnpj, processos in fornecedores.items():
            if len(processos) >= 5:  # Aparece em 5+ contratos
                self.alerts.append({
                    "regra": 6,
                    "tipo": self.ALERT_RULES[6],
                    "cnpj_fornecedor": cnpj,
                    "quantidade_contratos": len(processos),
                    "descricao": f"Fornecedor aparece em {len(processos)} contratos",
                    "risco": "MEDIUM",
                    "icon": self.RISK_LEVELS["MEDIUM"]
                })
    
    def _regra_7_valores_suspeitos(self, contratos: List[Dict]):
        """Regra 7: Valores suspeitos por setor/tipo"""
        # Análise por modalidade/tipo
        por_tipo = {}
        
        for contrato in contratos:
            tipo = contrato.get('modalidade', 'Indefinido')
            valor = contrato.get('valor_contratado', 0)
            
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(valor)
        
        # Detectar anomalias em cada setor
        for tipo, valores in por_tipo.items():
            if len(valores) < 3:
                continue
            
            try:
                media = mean(valores)
                q1 = quantiles(valores, n=4)[0]
                q3 = quantiles(valores, n=4)[2]
                iqr = q3 - q1
                limite_inferior = q1 - (1.5 * iqr)
                limite_superior = q3 + (1.5 * iqr)
                
                for contrato in contratos:
                    if contrato.get('modalidade') == tipo:
                        valor = contrato.get('valor_contratado', 0)
                        
                        if valor < limite_inferior or valor > limite_superior:
                            self.alerts.append({
                                "regra": 7,
                                "tipo": self.ALERT_RULES[7],
                                "numero_processo": contrato.get('numero_processo'),
                                "modalidade": tipo,
                                "valor": valor,
                                "valor_medio_setor": media,
                                "descricao": f"Valor atípico em {tipo}: R$ {valor:,.2f}",
                                "risco": "MEDIUM",
                                "icon": self.RISK_LEVELS["MEDIUM"]
                            })
            except Exception as e:
                logger.error(f"Erro na regra 7 para {tipo}: {e}")
    
    def _gerar_estatisticas(self, contratos: List[Dict]) -> Dict:
        """Gera estatísticas técnicas sobre os contratos"""
        valores = [c.get('valor_contratado', 0) for c in contratos if c.get('valor_contratado')]
        
        if not valores:
            return {}
        
        try:
            stats = {
                "total_contratos": len(contratos),
                "valor_total": sum(valores),
                "valor_medio": mean(valores),
                "valor_mediano": median(valores),
                "valor_minimo": min(valores),
                "valor_maximo": max(valores),
                "desvio_padrao": stdev(valores) if len(valores) > 1 else 0
            }
            
            # Quartis
            if len(valores) >= 4:
                quartis = quantiles(valores, n=4)
                stats["q1"] = quartis[0]
                stats["q2"] = quartis[1]
                stats["q3"] = quartis[2]
            
            return stats
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
    
    def _gerar_resumo_risco(self, contratos: List[Dict]) -> Dict:
        """Gera resumo de risco dos contratos"""
        total_alertas = len(self.alerts)
        alertas_altos = len([a for a in self.alerts if a.get('risco') == 'HIGH'])
        alertas_medios = len([a for a in self.alerts if a.get('risco') == 'MEDIUM'])
        alertas_baixos = len([a for a in self.alerts if a.get('risco') == 'LOW'])
        
        return {
            "total_alertas": total_alertas,
            "alertas_altos": alertas_altos,
            "alertas_medios": alertas_medios,
            "alertas_baixos": alertas_baixos,
            "percentual_contratos_com_alerta": (total_alertas / len(contratos) * 100) if contratos else 0,
            "risco_geral": self._classificar_risco_geral(alertas_altos, alertas_medios, len(contratos))
        }
    
    def _classificar_risco_geral(self, altos: int, medios: int, total: int) -> str:
        """Classifica risco geral da análise"""
        percentual_alertos = ((altos * 2 + medios) / max(total, 1)) * 100
        
        if percentual_alertos > 50:
            return "🔴 ALTO"
        elif percentual_alertos > 20:
            return "🟡 MÉDIO"
        else:
            return "🟢 BAIXO"
