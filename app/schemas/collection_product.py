from pydantic import BaseModel


class CollectionProductLinkOut(BaseModel):
    collection_id: int
    product_id: int

