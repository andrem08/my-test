import { css } from "styled-components"

export const cardStyles = css`
  background: linear-gradient(155deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 245, 239, 0.96) 100%);
  border: 1px solid rgba(106, 76, 51, 0.15);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(36, 25, 18, 0.12);
`

export const primaryButtonStyles = css`
  border: 1px solid rgba(122, 16, 16, 0.24);
  line-height: 1.15;
  font-family: "Manrope", "Segoe UI", sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: linear-gradient(130deg, #a21515 0%, #7a1010 100%);
  padding: 12px 18px;
  text-transform: uppercase;
  border-radius: 12px;
  color: #fff9f6;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.2s ease, filter 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.05);
    box-shadow: 0 8px 18px rgba(122, 16, 16, 0.3);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:focus-visible {
    outline: 3px solid rgba(18, 136, 255, 0.38);
    outline-offset: 2px;
  }

  &:disabled {
    opacity: 0.62;
    cursor: not-allowed;
  }
`
