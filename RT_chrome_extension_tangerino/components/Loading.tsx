import React from 'react';
import FourSquare from 'react-loading-indicators/FourSquare';
import styled from 'styled-components';




const LoadingAnimationBox = styled.div`
  border-radius: 50%; 

`;

const LoadingAnimation =() => {
  return <LoadingAnimationBox><FourSquare color="#942b2b" size="medium" text="" textColor="" /> </LoadingAnimationBox>;
};

export default LoadingAnimation;