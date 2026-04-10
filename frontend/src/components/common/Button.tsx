import type { ButtonHTMLAttributes } from "react";
import styles from "../../styles/common.module.css";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?: "small" | "medium" | "large";
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  size = "medium",
  fullWidth = false,
  className,
  children,
  ...rest
}: ButtonProps) {
  const classNames = [
    styles.button,
    styles[variant],
    size !== "medium" ? styles[size] : "",
    fullWidth ? styles.fullWidth : "",
    className ?? "",
  ].filter(Boolean).join(" ");

  return (
    <button className={classNames} {...rest}>
      {children}
    </button>
  );
}
