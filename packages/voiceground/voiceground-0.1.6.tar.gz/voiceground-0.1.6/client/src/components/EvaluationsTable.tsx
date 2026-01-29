import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/DataTable';
import { Evaluation } from '@/types';
import { CheckCircle2, XCircle, Circle } from 'lucide-react';

interface EvaluationsTableProps {
  evaluations: Evaluation[];
}

export function EvaluationsTable({ evaluations }: EvaluationsTableProps) {
  const columns = useMemo(
    () => [
      {
        header: 'Evaluation',
        cell: (evaluation: Evaluation) => (
          <div className="font-medium">{evaluation.name}</div>
        ),
        className: 'w-[200px]',
      },
      {
        header: 'Result',
        cell: (evaluation: Evaluation) => {
          if (evaluation.type === 'boolean') {
            const passed = evaluation.passed;
            if (passed === true) {
              return (
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="font-medium">Passed</span>
                </div>
              );
            } else if (passed === false) {
              return (
                <div className="flex items-center gap-2 text-red-500">
                  <XCircle className="h-4 w-4" />
                  <span className="font-medium">Failed</span>
                </div>
              );
            } else {
              return (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Circle className="h-4 w-4" />
                  <span>N/A</span>
                </div>
              );
            }
          } else if (evaluation.type === 'category') {
            return (
              <Badge variant="secondary">
                {evaluation.category || 'N/A'}
              </Badge>
            );
          } else if (evaluation.type === 'rating') {
            return (
              <div className="font-medium">
                {evaluation.rating ? `${evaluation.rating}/5` : 'N/A'}
              </div>
            );
          }
          
          return <span className="text-muted-foreground">N/A</span>;
        },
        className: 'w-[150px]',
      },
      {
        header: 'Reasoning',
        cell: (evaluation: Evaluation) => (
          <div className="text-sm text-muted-foreground">
            {evaluation.reasoning}
          </div>
        ),
      },
    ],
    []
  );

  if (evaluations.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="font-medium mb-1">No evaluations recorded</p>
          <p className="text-xs">No evaluations were configured for this conversation.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col min-h-0 overflow-hidden">
      <DataTable
        columns={columns}
        data={evaluations}
        emptyMessage="No evaluations recorded"
        getRowKey={(evaluation) => evaluation.name}
      />
      <p className="text-xs text-muted-foreground mt-4 flex-shrink-0">
        Showing {evaluations.length} evaluation{evaluations.length !== 1 ? 's' : ''}
      </p>
    </div>
  );
}
