import React, { useEffect, useMemo, useState } from "react";
import { FaCircle } from "react-icons/fa";
import styled, { css } from "styled-components";
const IconStatusBlock = styled.div `
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: gray;
  font-size: 1.5rem;
  text-shadow: 0 0 10px gray;

  i {
    color: gray;
    font-size: 2rem;
    text-shadow: 0 0 10px gray;
    background-color: gray;
  }
`;
const IconStatusFrezze = styled.div `
  display: flex;
  flex-direction: column;
  justify-content: center;
  /* trunk-ignore(git-diff-check/error) */
  color: #17dcff;
  font-size: 1.5rem;
  text-shadow: 0 0 10px #17dcff;

  i {
    color: #17dcff;
    font-size: 2rem;
    text-shadow: 0 0 10px #17dcff;
    background-color: #17dcff;
  }
`;
const IconStatusError = styled.div `
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #ec4646;
  font-size: 1.5rem;
  text-shadow: 0 0 10px #ec4646;

  i {
    color: #ec4646;
    font-size: 2rem;
    text-shadow: 0 0 10px gray;
    background-color: #ec4646;
  }
`;
const IconStatusRunning = styled.div `
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #ffa726;
  font-size: 1.5rem;
  text-shadow: 0 0 10px #f57c00;

  i {
    color: #ffa726;
    font-size: 2rem;
    text-shadow: 0 0 10px #f57c00;
    background-color: #ffa726;
  }
`;
const IconStatusRunned = styled.div `
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #388e3c;
  font-size: 1.5rem;
  text-shadow: 0 0 10px #2b692e;

  i {
    color: #388e3c;
    font-size: 2rem;
    text-shadow: 0 0 10px #2b692e;
    background-color: #388e3c;
  }
`;
export default function StatusIcon({ status }: {
    status: number;
}) {
    if (status === 1) {
        return (<IconStatusRunning>
        <FaCircle />
      </IconStatusRunning>);
    }
    if (status === 2) {
        return (<IconStatusRunned>
        <FaCircle />
      </IconStatusRunned>);
    }
    if (status === 0) {
        return (<IconStatusBlock>
        <FaCircle />
      </IconStatusBlock>);
    }
    if (status === 3) {
        return (<IconStatusFrezze>
        <FaCircle />
      </IconStatusFrezze>);
    }
    if (status === -1) {
        return (<IconStatusError>
        <FaCircle />
      </IconStatusError>);
    }
    return (<IconStatusError>
      <FaCircle />
    </IconStatusError>);
}
