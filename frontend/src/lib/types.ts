export type Vote = {
  option: string;
  score: number;
  winning_idx: number;
  scores: number[];
  reason: string;
};

export type RoundSide = {
  user: string;
  side: string;
  argument: string;
};

export type DebateRound = {
  round: number;
  most_confident: RoundSide;
  least_confident: RoundSide;
};

export type DebateOptions = {
  neutral_question: string;
  option_a: string;
  option_b: string;
};

export type FinalPayload = {
  options: DebateOptions;
  votes: {
    before: Record<string, Vote>;
    after: Record<string, Vote>;
  };
  debate: {
    round_count: number;
    most_confident_user: string;
    least_confident_user: string;
    rounds: DebateRound[];
    error?: string;
  };
};

export type StreamEvent = {
  type: string;
  stage: string;
  timestamp?: string;
  request_id?: string;
  data?: unknown;
  progress?: {
    completed: number;
    total: number;
  };
};
