from resonitelink.models.datamodel import Component, Member
from resonitelink.proxies import Proxy


class ComponentProxy(Proxy[Component]):
    
    async def fetch_data(self) -> Component:
        return await self.client.get_component(self.id)
    
    async def update_members(self, **members : Member):
        return await self.client.update_component(component=self.id, **members)
