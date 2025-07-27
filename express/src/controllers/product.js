import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

function coerceProductFields(data) {
  return {
    ...data,
    price: data.price !== undefined ? Number(data.price) : undefined,
    stock: data.stock !== undefined ? Number(data.stock) : undefined,
  };
}

export const createProduct = async (req, res, next) => {
  try {
    const product = await prisma.product.create({ data: coerceProductFields(req.body) });
    res.status(201).json(product);
  } catch (err) {
    next(err);
  }
};

export const getProduct = async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    const product = await prisma.product.findUnique({ where: { id } });
    if (!product) return res.status(404).json({ error: 'Product not found' });
    res.json(product);
  } catch (err) {
    next(err);
  }
};

export const listProducts = async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 100;
    const offset = parseInt(req.query.offset, 10) || 0;
    const products = await prisma.product.findMany({ skip: offset, take: limit });
    res.json(products);
  } catch (err) {
    next(err);
  }
};

export const updateProduct = async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    const product = await prisma.product.update({ where: { id }, data: coerceProductFields(req.body) });
    res.json(product);
  } catch (err) {
    if (err.code === 'P2025') return res.status(404).json({ error: 'Product not found' });
    next(err);
  }
};

export const deleteProduct = async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    await prisma.product.delete({ where: { id } });
    res.json({ ok: true });
  } catch (err) {
    if (err.code === 'P2025') return res.status(404).json({ error: 'Product not found' });
    next(err);
  }
};
