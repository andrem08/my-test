import React, { useState, useEffect } from 'react';
import styled from "styled-components";

const ProgressBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center; 
  width: 100%; 
  padding: 1.4rem;
`;

const ProgressElementsBar = styled.div`
  display: flex;
  align-items: center; 
  justify-content: center;
  gap: 1rem;
  width: 80%; 
`;


const StyledProgress = styled.progress`

  appearance: none;
  width: 120px;
  height: 1rem;
  border: 1px solid #ccc;
  border-radius: 10px;
  overflow: hidden; 

  &::-webkit-progress-bar {
    background-color: #f0f0f0;
    border-radius: 10px;
  }


  &::-webkit-progress-value {

    background-color: ${props => (props.value === props.max ? '#4caf50' : '#ffa726')};
    border-radius: 10px;
    transition: background-color 0.5s, width 0.3s ease-in-out; 
  }


  &::-moz-progress-bar {
    background-color: ${props => (props.value === props.max ? '#4caf50' : '#ffa726')};
    border-radius: 10px;
  }
`;

const PercentageSpan = styled.span`
  font-family: sans-serif;
  font-weight: bold;
  color: #333;
  min-width: 40px; 
  text-align: right;
`;


const RegularBillsProgressBar = () => {
    const [progress, setProgress] = useState(0);
    const [total, setTotal] = useState(0);
    const [label, setLabel] = useState('');

    useEffect(() => {
        const listener = (changes) => {
            if (changes.frequentBillsProgress) {
                const { progress, total, label } = changes.frequentBillsProgress.newValue;
                setProgress(progress);
                setTotal(total);
                setLabel(label);
            }
        };

        chrome.storage.local.get('frequentBillsProgress', (result) => {
            if (result.frequentBillsProgress) {
                const { progress, total, label } = result.frequentBillsProgress;
                setProgress(progress);
                setTotal(total);
                setLabel(label);
            }
        });

        chrome.storage.onChanged.addListener(listener);

        return () => {
            chrome.storage.onChanged.removeListener(listener);
        };
    }, []);

    if (total === 0) {
        return null;
    }

    const percentage = Math.floor((progress / total) * 100);

    return (
        <ProgressBarContainer>
            <ProgressElementsBar>
                <StyledProgress value={progress} max={total} />
                <PercentageSpan>{percentage}%</PercentageSpan>
            </ProgressElementsBar>
        </ProgressBarContainer>
    );
};

export default RegularBillsProgressBar;