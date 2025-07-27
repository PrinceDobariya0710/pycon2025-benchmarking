import express from "express";
import { plainText, jsonHello, fortune } from "../controllers/basic.js";

const router = express.Router();

router.get("/plain-text", plainText);
router.get("/json", jsonHello);
router.get("/fortune", fortune);

export default router;
