from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any


@dataclass
class _DetailModel:
    message: str
    error: str | None = None


@dataclass
class _AppErrorResponseModel:
    detail: _DetailModel


class _GenericResponseModel:
    def __class_getitem__(cls, _item: Any) -> type["_GenericResponseModel"]:
        return cls

    @classmethod
    def model_validate(cls, payload: Any) -> Any:
        return payload


class _PaginatedResponse:
    def __class_getitem__(cls, _item: Any) -> type["_PaginatedResponse"]:
        return cls


@dataclass
class _ModelDumpMixin:
    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        data = dict(self.__dict__)
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        return data


@dataclass
class _UserLoginModel:
    email: str
    password: str


@dataclass
class _UserCreateModel:
    email: str
    password: str
    name: str | None = None


@dataclass
class _UserUpdateModel:
    name: str | None = None


@dataclass
class _UserReadModel:
    id: str | None = None
    email: str | None = None


@dataclass
class _TokenResponseModel:
    token: str | None = None


@dataclass
class _UserQueryParams:
    limit: int | None = None


@dataclass
class _CompanyCreateModel(_ModelDumpMixin):
    name: str | None = None
    description: str | None = None
    industry: str | None = None
    phone_number: str | None = None
    email: str | None = None
    address: str | None = None


@dataclass
class _CompanyUpdateModel(_ModelDumpMixin):
    name: str | None = None
    description: str | None = None
    industry: str | None = None
    phone_number: str | None = None
    address: str | None = None


@dataclass
class _CompanyReadModel:
    id: int | None = None
    name: str | None = None


@dataclass
class _CompanyQueryParamsModel(_ModelDumpMixin):
    limit: int | None = None
    page: int | None = None
    role_name: str | None = None
    name: str | None = None
    description: str | None = None
    industry: str | None = None
    email: str | None = None


def _ensure_module(name: str) -> ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = ModuleType(name)
        module.__path__ = []
        sys.modules[name] = module
    return module


# Provide minimal stubs for external dependencies used by the client.
_ensure_module("sverse_generic_models")
app_error_module = _ensure_module("sverse_generic_models.app_error")
generic_response_module = _ensure_module("sverse_generic_models.generic_response")
generic_pagination_module = _ensure_module("sverse_generic_models.generic_pagination")
app_error_module.AppErrorResponseModel = _AppErrorResponseModel
app_error_module.DetailModel = _DetailModel
generic_response_module.GenericResponseModel = _GenericResponseModel
generic_pagination_module.PaginatedResponse = _PaginatedResponse

_ensure_module("userverse_models")
user_module = _ensure_module("userverse_models.user")
user_user_module = _ensure_module("userverse_models.user.user")
user_user_module.UserLoginModel = _UserLoginModel
user_user_module.UserUpdateModel = _UserUpdateModel
user_user_module.UserCreateModel = _UserCreateModel
user_user_module.UserReadModel = _UserReadModel
user_user_module.TokenResponseModel = _TokenResponseModel
user_user_module.UserQueryParams = _UserQueryParams
user_module.user = user_user_module

company_module = _ensure_module("userverse_models.company")
company_company_module = _ensure_module("userverse_models.company.company")
company_company_module.CompanyCreateModel = _CompanyCreateModel
company_company_module.CompanyUpdateModel = _CompanyUpdateModel
company_company_module.CompanyReadModel = _CompanyReadModel
company_company_module.CompanyQueryParamsModel = _CompanyQueryParamsModel
company_module.company = company_company_module
