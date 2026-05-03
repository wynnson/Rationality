"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

import type { DebateRound, FinalPayload, StreamEvent, Vote } from "@/lib/types";

type StartArgs = {
  url: string;
  debate_question: string;
};

export function useDebateStream() {
  const abortRef = useRef<AbortController | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("idle");
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [beforeVotes, setBeforeVotes] = useState<Record<string, Vote>>({});
  const [afterVotes, setAfterVotes] = useState<Record<string, Vote>>({});
  const [rounds, setRounds] = useState<DebateRound[]>([]);
  const [options, setOptions] = useState<FinalPayload["options"] | null>(null);
  const [finalPayload, setFinalPayload] = useState<FinalPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setStatus("idle");
    setEvents([]);
    setBeforeVotes({});
    setAfterVotes({});
    setRounds([]);
    setOptions(null);
    setFinalPayload(null);
    setError(null);
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsLoading(false);
  }, []);

  const start = useCallback(async ({ url, debate_question }: StartArgs) => {
    stop();
    reset();
    setIsLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await fetchEventSource("/api/debate/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, debate_question }),
        signal: controller.signal,
        openWhenHidden: true,
        onmessage(event) {
          const payload = JSON.parse(event.data) as StreamEvent;
          setEvents((prev) => [...prev, payload]);
          setStatus(payload.stage || event.event);

          if (payload.type === "options" && payload.data) {
            setOptions(payload.data as FinalPayload["options"]);
            return;
          }

          if (payload.type === "vote_partial" && payload.data) {
            const voteData = payload.data as { user: string; vote: Vote };
            if (payload.stage === "before") {
              setBeforeVotes((prev) => ({ ...prev, [voteData.user]: voteData.vote }));
            } else {
              setAfterVotes((prev) => ({ ...prev, [voteData.user]: voteData.vote }));
            }
            return;
          }

          if (payload.type === "debate_round" && payload.data) {
            const round = payload.data as DebateRound;
            setRounds((prev) => [...prev, round]);
            return;
          }

          if (payload.type === "final" && payload.data) {
            const final = payload.data as FinalPayload;
            setFinalPayload(final);
            setOptions(final.options);
            setBeforeVotes(final.votes.before);
            setAfterVotes(final.votes.after);
            setRounds(final.debate.rounds);
            setIsLoading(false);
            return;
          }

          if (payload.type === "error") {
            const detail =
              typeof payload.data === "object" && payload.data !== null
                ? String((payload.data as { detail?: string }).detail ?? "Unknown error")
                : "Unknown error";
            setError(detail);
            setIsLoading(false);
          }
        },
        onerror(err) {
          setError(err.message || "Stream failed");
          setIsLoading(false);
          throw err;
        },
        onclose() {
          setIsLoading(false);
        },
      });
    } catch (err) {
      if (controller.signal.aborted) {
        return;
      }
      const message = err instanceof Error ? err.message : "Stream failed";
      setError(message);
      setIsLoading(false);
    }
  }, [reset, stop]);

  const changedVoters = useMemo(() => {
    return Object.keys(beforeVotes).filter(
      (user) => beforeVotes[user]?.winning_idx !== afterVotes[user]?.winning_idx,
    );
  }, [afterVotes, beforeVotes]);

  return {
    isLoading,
    status,
    events,
    options,
    beforeVotes,
    afterVotes,
    rounds,
    finalPayload,
    changedVoters,
    error,
    start,
    stop,
    reset,
  };
}
