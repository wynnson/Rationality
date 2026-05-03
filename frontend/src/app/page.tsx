"use client";

import { FormEvent, useMemo, useState } from "react";
import { Loader2, PauseCircle, PlayCircle, Radar } from "lucide-react";
import dynamic from "next/dynamic";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useDebateStream } from "@/hooks/use-debate-stream";

const VoteCharts = dynamic(
  () => import("@/components/vote-charts").then((mod) => mod.VoteCharts),
  { ssr: false },
);

function VoteTable({
  title,
  votes,
}: {
  title: string;
  votes: Record<string, { option: string; score: number; reason: string }>;
}) {
  const rows = Object.entries(votes).sort((a, b) => b[1].score - a[1].score);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{rows.length} voters</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {rows.length === 0 ? (
          <p className="text-sm text-slate-500">No votes yet.</p>
        ) : (
          rows.map(([user, vote]) => (
            <div key={user} className="rounded-lg border border-slate-200 p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="font-medium text-slate-900">{user}</p>
                <Badge variant="secondary">{vote.score.toFixed(2)}</Badge>
              </div>
              <p className="text-sm text-slate-700">{vote.option}</p>
              <p className="mt-2 text-xs text-slate-500">{vote.reason}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [debateQuestion, setDebateQuestion] = useState("");
  const {
    isLoading,
    status,
    events,
    options,
    beforeVotes,
    afterVotes,
    rounds,
    changedVoters,
    error,
    start,
    stop,
  } = useDebateStream();

  const statusText = useMemo(() => status.replaceAll("_", " "), [status]);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await start({
      url,
      debate_question: debateQuestion,
    });
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-100 via-white to-slate-100 px-4 py-10">
      <div className="mx-auto max-w-6xl space-y-6">
        <Card className="border-slate-300">
          <CardHeader>
            <div className="flex items-center gap-2 text-slate-700">
              <Radar className="h-5 w-5" />
              <span className="text-sm uppercase tracking-wide">Rationality Stream</span>
            </div>
            <CardTitle className="text-2xl">Reddit Debate Simulator</CardTitle>
            <CardDescription>
              Stream each generation stage live: initial vote, 5 debate rounds, and revote.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={onSubmit}>
              <Input
                required
                placeholder="https://www.reddit.com/r/.../comments/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <Textarea
                required
                placeholder="What question should agents debate?"
                value={debateQuestion}
                onChange={(e) => setDebateQuestion(e.target.value)}
              />
              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Streaming...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="h-4 w-4" />
                      Start Stream
                    </>
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={stop} disabled={!isLoading}>
                  <PauseCircle className="h-4 w-4" />
                  Stop
                </Button>
                <Badge variant="outline">status: {statusText || "idle"}</Badge>
                <Badge variant="secondary">events: {events.length}</Badge>
              </div>
              {error ? <p className="text-sm text-red-600">{error}</p> : null}
            </form>
          </CardContent>
        </Card>

        {options ? (
          <Card>
            <CardHeader>
              <CardTitle>Question Framing</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-slate-700">
              <p><span className="font-medium">Neutral:</span> {options.neutral_question}</p>
              <p><span className="font-medium">Option A:</span> {options.option_a}</p>
              <p><span className="font-medium">Option B:</span> {options.option_b}</p>
            </CardContent>
          </Card>
        ) : null}

        <section className="grid gap-4 md:grid-cols-2">
          <VoteTable title="Before Debate" votes={beforeVotes} />
          <VoteTable title="After Debate" votes={afterVotes} />
        </section>

        <VoteCharts beforeVotes={beforeVotes} afterVotes={afterVotes} />

        <Card>
          <CardHeader>
            <CardTitle>Debate Rounds</CardTitle>
            <CardDescription>
              Completed rounds: {rounds.length} / 5 | Changed voters: {changedVoters.length}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {rounds.length === 0 ? (
              <p className="text-sm text-slate-500">Rounds will appear during generation.</p>
            ) : (
              rounds.map((round) => (
                <div key={round.round} className="rounded-lg border border-slate-200 p-4">
                  <p className="mb-3 text-sm font-semibold text-slate-900">Round {round.round}</p>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <p className="text-xs font-medium uppercase text-slate-500">Most Confident</p>
                      <p className="text-sm font-medium text-slate-800">{round.most_confident.user}</p>
                      <p className="text-xs text-slate-600">{round.most_confident.side}</p>
                      <p className="mt-2 text-sm text-slate-700">{round.most_confident.argument}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase text-slate-500">Least Confident</p>
                      <p className="text-sm font-medium text-slate-800">{round.least_confident.user}</p>
                      <p className="text-xs text-slate-600">{round.least_confident.side}</p>
                      <p className="mt-2 text-sm text-slate-700">{round.least_confident.argument}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
