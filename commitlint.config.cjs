module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "header-max-length": [2, "always", 72],
    "subject-case": [2, "never", ["pascal-case", "upper-case", "start-case"]],
    "scope-case": [2, "always", "kebab-case"],
  },
};

