import express from "express";
import {
  createProduct,
  getProduct,
  listProducts,
  updateProduct,
  deleteProduct
} from "../controllers/product.js";

const router = express.Router();

router.post("/", createProduct);
router.get("/", listProducts);
router.get("/:id", getProduct);
router.put("/:id", updateProduct);
router.delete("/:id", deleteProduct);

export default router;
