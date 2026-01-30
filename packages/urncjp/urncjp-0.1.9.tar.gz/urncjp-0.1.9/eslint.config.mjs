// @ts-check

import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import { globalIgnores } from "eslint/config";

export default tseslint.config(
  eslint.configs.recommended,
  tseslint.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          args: "none",
        },
      ],
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
  globalIgnores(["lib/**/*", "urncjp/labextension/static/**/*"]),
);
