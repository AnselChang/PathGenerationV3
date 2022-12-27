from Commands.Edge import Edge, StraightEdge, CurveEdge
from Commands.Node import *
from Commands.StartNode import StartNode
from Commands.TurnNode import TurnNode
from MouseInterfaces.Hoverable import Hoverable
from SingletonState.ReferenceFrame import PointRef, Ref
from SingletonState.SoftwareState import SoftwareState, Mode
import pygame, Utility, math
from typing import Iterator

"""
Stores a list of commands, which make up the path
"""

class Program:

    def __init__(self):
        self.nodes: list[Node] = [ StartNode(self) ]
        self.edges: list[Edge] = []
        self.recompute()
        
    def addNodeForward(self, position: PointRef):
        print("add node forward")
        self.nodes.append(TurnNode(self, position))
        self.edges.append(StraightEdge())
        self.recompute()

    def addNodeCurve(self, position: PointRef):

        self.nodes.append(TurnNode(self, position))
        self.edges.append(CurveEdge())
        self.recompute()

    def snapNewPoint(self, position: PointRef, node: Node = None) -> PointRef:

        SNAP_CONSTANT = 0.06

        if node is None:
            i = len(self.nodes)
        else:
            i = self.nodes.index(node)

        # If close, snap previous turn
        if i >= 2:
            before: 'Node' = self.nodes[i-1]
            currentHeading = Utility.thetaTwoPoints(before.position.fieldRef, position.fieldRef)

            if abs(Utility.deltaInHeading(currentHeading, before.beforeHeading)) < SNAP_CONSTANT:
                dist = Utility.distanceTuples(before.position.fieldRef, position.fieldRef)
                x = before.position.fieldRef[0] + dist * math.cos(before.beforeHeading)
                y = before.position.fieldRef[1] + dist * math.sin(before.beforeHeading)
                return PointRef(Ref.FIELD, (x,y))

        # If close, snap current turn
        if i < len(self.nodes) - 1:
            before: 'Node' = self.nodes[i-1]
            after: 'Node' = self.nodes[i+1]
            beforeHeading = Utility.thetaTwoPoints(before.position.fieldRef, position.fieldRef)
            nextHeading = Utility.thetaTwoPoints(position.fieldRef, after.position.fieldRef)

            diff = Utility.deltaInHeading(beforeHeading, nextHeading)
            if abs(diff) < SNAP_CONSTANT:

                newHeading = Utility.thetaTwoPoints(before.position.fieldRef, after.position.fieldRef)

                dist = Utility.distanceTuples(before.position.fieldRef, position.fieldRef)
                x = before.position.fieldRef[0] + dist * math.cos(newHeading)
                y = before.position.fieldRef[1] + dist * math.sin(newHeading)
                return PointRef(Ref.FIELD, (x,y))

        # If close, snap next turn
        if i < len(self.nodes) - 1 and self.nodes[i+1].afterHeading is not None:
            after: 'Node' = self.nodes[i+1]
            beforeHeading = Utility.thetaTwoPoints(position.fieldRef, after.position.fieldRef)
            
            diff = Utility.deltaInHeading(beforeHeading, after.afterHeading)
            if abs(diff) < SNAP_CONSTANT:

                dist = Utility.distanceTuples(position.fieldRef, after.position.fieldRef)
                x = after.position.fieldRef[0] - dist * math.cos(after.afterHeading)
                y = after.position.fieldRef[1] - dist * math.sin(after.afterHeading)
                return PointRef(Ref.FIELD, (x,y))

        return position.copy()

    def deleteNode(self, node: TurnNode):
        
        # Last node. just delete last segment and node
        if node.afterHeading is None:
            del self.nodes[-1]
            del self.edges[-1]
        else:
            # connect the previous and next node together
            i = self.nodes.index(node)
            del self.nodes[i]
            del self.edges[i]

        self.recompute()

    # recalculate all the state for each point/edge and command after the list of points is modified
    def recompute(self):
        if len(self.nodes) == 0:
            return
        elif len(self.nodes) == 1:
            self.nodes[0].compute(None, None)
            return

        heading = self.nodes[0].compute(None, self.nodes[1])
        for i in range(len(self.edges)):
            heading = self.edges[i].compute(heading, self.nodes[i].position, self.nodes[i+1].position)
            heading = self.nodes[i+1].compute(self.nodes[i], None if i == len(self.edges)-1 else self.nodes[i+2])

        # recompute commands
        x = Utility.SCREEN_SIZE + 17
        y = 18
        dy = 70
        for command in self.getHoverablesCommands():
            command.updatePosition(x, y)
            y += dy

    def getHoverablesPath(self) -> Iterator[Hoverable]:

        for node in self.nodes:
            yield node

        for edge in self.edges:
            yield edge

        return
        yield

    # Skip start node. Skip any nodes that don't turn
    def getHoverablesCommands(self) -> Iterator[Command]:

        if len(self.nodes) >= 2:
            for i in range(len(self.edges)):
                yield self.edges[i].command

                if self.nodes[i+1].hasTurn:
                    yield self.nodes[i+1].command

        return
        yield

    def drawPath(self, screen: pygame.Surface):

        # Draw the path
        for edge in self.edges:
            edge.draw(screen)
        for node in self.nodes:
            node.draw(screen)

    def drawCommands(self, screen: pygame.Surface):

        # Draw the commands
        for command in self.getHoverablesCommands():
            command.draw(screen)

