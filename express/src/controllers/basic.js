import { PrismaClient } from '@prisma/client';
import path from 'path';
const prisma = new PrismaClient();

export const plainText = (req, res) => {
  res.type('text/plain').send('Hello, world!');
};

export const jsonHello = (req, res) => {
  res.json({ message: 'Hello, world from JSON serialization endpoint!' });
};

export const fortune = async (req, res, next) => {
  try {
    const products = await prisma.product.findMany({ take: 100 });
    res.render('fortune', { products });
  } catch (err) {
    next(err);
  }
};
