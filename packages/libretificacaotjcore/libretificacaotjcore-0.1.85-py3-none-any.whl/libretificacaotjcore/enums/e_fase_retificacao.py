from enum import Enum


class EFaseRetificacao(Enum):
    NaoIniciado = 0
    SolicitacaoXml = 1
    DownloadXml = 2
    ExtraindoDadosDoXml = 3
    #? Abertura de Competencia
    EstruturandoXmlAberturaCompetencia = 4
    AberturaDeCompetencia = 5
    ConsultandoESocialAberturaCompetencia = 6
    #? Rubricas
    EstruturandoXmlInclusaoRubricas = 7
    InclusaoDasRubricas = 8
    ConsultandoESocialInclusaoRubricas = 9
    #? Exclusao de Pagamentos
    EstruturandoXmlExclusaoPagamentos = 10
    ExclusaoDePagamentos = 11
    ConsultandoESocialExclusaoPagamentos = 12
    #? Retificacao
    EstruturandoXmlRetificacaoRemuneracao = 13
    RetificacaoDaRemuneracao = 14
    ConsultandoESocialRetificacaoRemuneracao = 15
    #? Desligamento
    EstruturandoXmlDesligamento = 16
    Desligamento = 17
    ConsultandoESocialDesligamento = 18
    #? Inclusao de Pagamentos
    EstruturandoXmlInclusaoPagamentos = 19
    InclusaoDosPagamentos = 20
    ConsultandoESocialInclusaoPagamentos = 21
    #? Fechamento de Competencia
    EstruturandoXmlFechamentoCompetencia = 22
    FechamentoDeCompetencia = 23
    ConsultandoESocialFechamentoCompetencia = 24
    Finalizado = 25
