from pydantic.main import BaseModel
from typing import Optional


class AgentsCreatedAndModifiedResponse(BaseModel):
    createdAgents: int
    modifiedAgents: int


class AgentActivityPerDayItem(BaseModel):
    date: str
    createdAgents: int
    modifiedAgents: int


class AgentsCreatedAndModifiedPerDayResponse(BaseModel):
    agentsCreatedAndModifiedPerDay: list[AgentActivityPerDayItem]


class FlowsCreatedAndModifiedResponse(BaseModel):
    createdFlows: int
    modifiedFlows: int


class FlowActivityPerDayItem(BaseModel):
    date: str
    createdFlows: int
    modifiedFlows: int


class FlowsCreatedAndModifiedPerDayResponse(BaseModel):
    flowsCreatedAndModifiedPerDay: list[FlowActivityPerDayItem]


class ProcessesCreatedAndModifiedResponse(BaseModel):
    createdProcesses: int
    modifiedProcesses: int


class AgentUsagePerUserItem(BaseModel):
    userId: str
    userName: Optional[str] = None
    totalCost: float
    totalRequests: int
    totalTokens: int


class AgentUsagePerUserResponse(BaseModel):
    agentUsagePerUser: list[AgentUsagePerUserItem]


class AverageCostPerRequestResponse(BaseModel):
    averageCost: float


class AverageCostPerUserResponse(BaseModel):
    averageCost: float


class CostPerUserPerDateItem(BaseModel):
    date: str
    userId: str
    userName: Optional[str] = None
    averageCost: float


class AverageCostPerUserPerDateResponse(BaseModel):
    averageCostPerUserPerDate: list[CostPerUserPerDateItem]


class AverageRequestTimeResponse(BaseModel):
    averageTime: float


class AverageRequestsPerDayResponse(BaseModel):
    averageRequests: float


class AverageRequestsPerUserResponse(BaseModel):
    averageRequests: float


class RequestsPerUserPerDateItem(BaseModel):
    date: str
    userId: str
    userName: Optional[str] = None
    averageRequests: float


class AverageRequestsPerUserPerDateResponse(BaseModel):
    averageRequestsPerUserPerDate: list[RequestsPerUserPerDateItem]


class AverageTokensPerRequestResponse(BaseModel):
    averageInputTokens: float
    averageOutputTokens: float
    averageTotalTokens: float


class UsersPerAgentItem(BaseModel):
    agentName: str
    averageUsers: float


class AverageUsersPerAgentResponse(BaseModel):
    averageUsersPerAgent: list[UsersPerAgentItem]


class UsersPerProjectItem(BaseModel):
    projectId: str
    projectName: Optional[str] = None
    averageUsers: float


class AverageUsersPerProjectResponse(BaseModel):
    averageUsersPerProject: list[UsersPerProjectItem]


class NumberOfTokensResponse(BaseModel):
    totalInputTokens: int
    totalOutputTokens: int
    totalTokens: int


class TokensPerAgentItem(BaseModel):
    agentName: str
    model: str
    inputTokens: int
    outputTokens: int
    totalTokens: int


class NumberOfTokensPerAgentResponse(BaseModel):
    tokensPerAgent: list[TokensPerAgentItem]


class TokensPerDayItem(BaseModel):
    date: str
    inputTokens: int
    outputTokens: int
    totalTokens: int


class NumberOfTokensPerDayResponse(BaseModel):
    tokensPerDay: list[TokensPerDayItem]


class OverallErrorRateResponse(BaseModel):
    errorRate: float


class AgentByRequestsItem(BaseModel):
    agentName: str
    totalRequests: int


class Top10AgentsByRequestsResponse(BaseModel):
    topAgents: list[AgentByRequestsItem]


class AgentByTokensItem(BaseModel):
    agentName: str
    totalTokens: int


class Top10AgentsByTokensResponse(BaseModel):
    topAgents: list[AgentByTokensItem]


class UserByCostItem(BaseModel):
    userId: str
    userName: Optional[str] = None
    totalCost: float


class Top10UsersByCostResponse(BaseModel):
    topUsers: list[UserByCostItem]


class UserByRequestsItem(BaseModel):
    userId: str
    userName: Optional[str] = None
    totalRequests: int


class Top10UsersByRequestsResponse(BaseModel):
    topUsers: list[UserByRequestsItem]


class TotalActiveAgentsResponse(BaseModel):
    totalActiveAgents: int


class TotalActiveProjectsResponse(BaseModel):
    totalActiveProjects: int


class TotalActiveUsersResponse(BaseModel):
    totalActiveUsers: int


class TotalCostResponse(BaseModel):
    totalCost: float


class CostPerDayItem(BaseModel):
    date: str
    totalCost: float


class TotalCostPerDayResponse(BaseModel):
    costPerDay: list[CostPerDayItem]


class TotalRequestTimeResponse(BaseModel):
    totalTime: float


class TotalRequestsResponse(BaseModel):
    totalRequests: int


class RequestsPerDayItem(BaseModel):
    date: str
    totalRequests: int
    totalRequestsWithError: int


class TotalRequestsPerDayResponse(BaseModel):
    requestsPerDay: list[RequestsPerDayItem]


class TotalRequestsWithErrorResponse(BaseModel):
    totalRequestsWithError: int


class TotalTokensResponse(BaseModel):
    totalInputTokens: int
    totalOutputTokens: int
    totalTokens: int
