import React from "react"
import FourSquare from "react-loading-indicators/FourSquare"
import styled from "styled-components"

const LoadingAnimationBox = styled.div`
  display: grid;
  place-items: center;
  min-height: 110px;
`

const LoadingAnimation = () => {
  return (
    <LoadingAnimationBox>
      <FourSquare color="#8d1919" size="medium" text="" textColor="" />
    </LoadingAnimationBox>
  )
}

export default LoadingAnimation