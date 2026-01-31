from django.utils.translation import gettext_lazy as _
from djangoldp import fields
from djangoldp_edc.permissions import EdcContractPermissionV3
from djangoldp_i18n.views import I18nLDPViewSet

from djangoldp_ds4go.models.__base_named_model import baseNamedModel
from djangoldp_ds4go.models.category import Category
from djangoldp_ds4go.models.fact import Fact


class FactBundle(baseNamedModel):
    description = fields.TextField(blank=True, null=True, verbose_name=_("Description"))
    facts = fields.ManyToManyField(Fact, blank=True, verbose_name=_("Facts"), rdf_type="ldp:contains")

    class Meta(baseNamedModel.Meta):
        depth = 2
        permission_classes = [EdcContractPermissionV3]
        verbose_name = _("Facts Bundle")
        verbose_name_plural = _("Facts Bundles")

        rdf_type = ["ldp:Container", "ds4go:FactBundle"]
        serializer_fields = baseNamedModel.Meta.serializer_fields + [
            "description",
            "facts",
        ]

        view_set = I18nLDPViewSet
