import uuid

from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base


class ProductSkuMapping(Base):
    __tablename__ = "product_sku_mapping"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String, nullable=False, unique=True)
    medusa_product_id = Column(String, nullable=False)
    erp_product_id = Column(String, nullable=False)
    shopify_product_id = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    def __repr__(self):
        return f"<ProductInventory(id={self.id}, warehouse_id={self.warehouse_id}), sku={self.sku}, quantity={self.quantity}>"

class Product(Base):
    __tablename__ = "product"

    clk_product_id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sku = Column(String(64), nullable=False, unique=True)
    platform_mappings = relationship("ProductPlatformMap",back_populates="product",cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_product_sku", "sku"),
    )

    def __repr__(self):
        return f"<Product(id={self.clk_product_id}, sku={self.sku})>"


class ProductPlatformMap(Base):
    __tablename__ = "product_platform_map"

    clk_product_id = Column(UUID(as_uuid=True),ForeignKey("product.clk_product_id", ondelete="CASCADE"),primary_key=True)
    platform_type = Column(String(32), nullable=False)
    product_id = Column(String(64), nullable=False)
    variant_id = Column(String(64), nullable=False)

    product = relationship(
        "Product",
        back_populates="platform_mappings"
    )

    __table_args__ = (
        PrimaryKeyConstraint("platform_type","variant_id"),
        Index("ix_product_platform_type", "platform_type"),
    )

    def __repr__(self):
        return (
            f"<ProductPlatformMap(clk_product_id={self.clk_product_id}, "
            f"platform_type={self.platform_type},variant_id={self.variant_id})>"
        )