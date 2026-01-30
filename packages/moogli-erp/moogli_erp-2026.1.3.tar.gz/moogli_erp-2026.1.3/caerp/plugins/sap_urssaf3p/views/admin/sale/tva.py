from caerp.plugins.sap_urssaf3p.forms.tva import sap_urssaf3p_get_tva_edit_schema
from caerp.views.admin.sale.accounting.tva import TvaAddView, TvaEditView, TvaListView


class SapUrssaf3pTvaAddView(TvaAddView):
    def get_schema(self):
        return sap_urssaf3p_get_tva_edit_schema(self.request)


class SapUrssaf3pTvaEditView(TvaEditView):
    def get_schema(self):
        return sap_urssaf3p_get_tva_edit_schema(self.request, self.context)


def includeme(config):
    # Status View
    config.add_admin_view(
        SapUrssaf3pTvaAddView,
        parent=TvaListView,
        request_param="action=add",
        renderer="admin/crud_add_edit.mako",
    )
    config.add_admin_view(
        SapUrssaf3pTvaEditView,
        parent=TvaListView,
        renderer="admin/crud_add_edit.mako",
    )
