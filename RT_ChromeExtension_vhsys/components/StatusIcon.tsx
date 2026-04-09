import React from "react"
import { FaCircle } from "react-icons/fa"
import styled from "styled-components"

const STATUS_COLOR_BY_CODE: Record<number, string> = {
  [-1]: "#d04545",
  0: "#6f6f6f",
  1: "#f4a13c",
  2: "#2f9b55",
  3: "#17dcff"
}

const StatusIconWrap = styled.div<{ $color: string }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: ${({ $color }) => $color};

  svg {
    font-size: 1.05rem;
    filter: drop-shadow(0 0 8px ${({ $color }) => $color});
  }
`

export default function StatusIcon({ status }: { status: number }) {
  const color = STATUS_COLOR_BY_CODE[status] ?? STATUS_COLOR_BY_CODE[-1]

  return (
    <StatusIconWrap
      $color={color}
      aria-label={`Status ${status}`}
      title={`Status ${status}`}>
      <FaCircle />
    </StatusIconWrap>
  )
}
