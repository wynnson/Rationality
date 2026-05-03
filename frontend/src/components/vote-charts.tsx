"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Vote } from "@/lib/types";

export function VoteCharts({
  beforeVotes,
  afterVotes,
}: {
  beforeVotes: Record<string, Vote>;
  afterVotes: Record<string, Vote>;
}) {
  const scoreShiftData = Object.keys(beforeVotes)
    .filter((user) => afterVotes[user])
    .map((user) => ({
      user,
      before: beforeVotes[user].score,
      after: afterVotes[user].score,
    }))
    .sort((a, b) => b.before - a.before);

  const beforeCounts = { option_a: 0, option_b: 0 };
  const afterCounts = { option_a: 0, option_b: 0 };

  Object.values(beforeVotes).forEach((vote) => {
    if (vote.winning_idx === 0) {
      beforeCounts.option_a += 1;
    } else {
      beforeCounts.option_b += 1;
    }
  });

  Object.values(afterVotes).forEach((vote) => {
    if (vote.winning_idx === 0) {
      afterCounts.option_a += 1;
    } else {
      afterCounts.option_b += 1;
    }
  });

  const optionShiftData = [
    {
      phase: "Before",
      optionA: beforeCounts.option_a,
      optionB: beforeCounts.option_b,
    },
    {
      phase: "After",
      optionA: afterCounts.option_a,
      optionB: afterCounts.option_b,
    },
  ];

  const scoreChartRef = useRef<HTMLDivElement | null>(null);
  const optionChartRef = useRef<HTMLDivElement | null>(null);
  const [scoreChartWidth, setScoreChartWidth] = useState(0);
  const [optionChartWidth, setOptionChartWidth] = useState(0);

  useEffect(() => {
    const scoreNode = scoreChartRef.current;
    const optionNode = optionChartRef.current;
    if (!scoreNode || !optionNode) {
      return;
    }

    const updateSizes = () => {
      setScoreChartWidth(scoreNode.clientWidth);
      setOptionChartWidth(optionNode.clientWidth);
    };

    updateSizes();

    const observer = new ResizeObserver(updateSizes);
    observer.observe(scoreNode);
    observer.observe(optionNode);

    return () => observer.disconnect();
  }, []);

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Confidence Shift by User</CardTitle>
          <CardDescription>Each voter&apos;s confidence before vs after debate</CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <div ref={scoreChartRef} className="h-full w-full min-w-0">
            {scoreChartWidth > 0 ? (
              <BarChart width={scoreChartWidth} height={320} data={scoreShiftData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="user" hide />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="before" fill="#334155" name="Before" radius={[4, 4, 0, 0]} />
                <Bar dataKey="after" fill="#0f766e" name="After" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Option Share Shift</CardTitle>
          <CardDescription>How many voters picked each option before and after</CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <div ref={optionChartRef} className="h-full w-full min-w-0">
            {optionChartWidth > 0 ? (
              <BarChart width={optionChartWidth} height={320} data={optionShiftData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="phase" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey="optionA" fill="#1d4ed8" name="Option A" radius={[4, 4, 0, 0]} />
                <Bar dataKey="optionB" fill="#b91c1c" name="Option B" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
