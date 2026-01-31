<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"		
  exclude-result-prefixes="">
    
<!-- ## entretien ## préfiguration des <sp> -->
<xsl:template match="text:p[@text:style-name='TEI_speaker']">
    <start type="sp">
        <xsl:attribute name="rend">
            <xsl:choose>
                <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_question']">question</xsl:when>
                <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_versifiedreplica']"/>
                <xsl:when test="following-sibling::text:p[1][starts-with(@text:style-name,'TEI_replica')]"/>
                <xsl:when test="following-sibling::text:p[1][starts-with(@text:style-name,'TEI_didascaly')]"/>
                <xsl:otherwise>answer</xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </start>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_question']">
    <xsl:choose>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_speaker']"></xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_question']"></xsl:when>
        <xsl:otherwise><start type="sp" rend="question"/></xsl:otherwise>
    </xsl:choose>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
    <xsl:choose>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_question']"></xsl:when>
        <xsl:otherwise><end type="sp"/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_answer']">
    <xsl:choose>
        <xsl:when test="child::text:span[@text:style-name='TEI_speaker-inline']">
            <start type="sp" rend="answer"/>
        </xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_speaker']"></xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_answer']"/>
        <xsl:otherwise><start type="sp" rend="answer"/></xsl:otherwise>
    </xsl:choose>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
    <xsl:choose>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_answer'][child::text:span[@text:style-name='TEI_speaker-inline']]"><end type="sp"/></xsl:when>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_answer']"></xsl:when>
        <xsl:otherwise><end type="sp"/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_versifiedreplica']">
    <xsl:choose>
        <xsl:when test="child::text:span[@text:style-name='TEI_speaker-inline']">
            <start type="sp"/><!-- rend="versifiedreplica" -->
        </xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_speaker']"></xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_didascaly'] and preceding-sibling::text:p[2][@text:style-name='TEI_speaker']"></xsl:when>
<!--        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_versifiedreplica']"/>-->
        <xsl:otherwise><start type="sp"/><!-- rend="versifiedreplica"--></xsl:otherwise>
    </xsl:choose>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
    <xsl:choose>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference'] and following-sibling::text:*[1][@text:style-name='TEI_bibl_start']"><end type="sp"/></xsl:when>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference'] and not(following-sibling::text:*[1][@text:style-name='TEI_bibl_start'])"/>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_versifiedreplica'][child::text:span[@text:style-name='TEI_speaker-inline']]"><end type="sp"/></xsl:when>
<!--        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_versifiedreplica']"></xsl:when>-->
        <xsl:otherwise><end type="sp"/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_replica')]">
<!--
    <xsl:comment>TEI_replica</xsl:comment>
    <xsl:comment>1st preceding-sibling local name = <xsl:value-of select="preceding-sibling::*[1]/local-name()"/></xsl:comment>
-->
    <xsl:choose>
        <!-- lorsqu'il s'agit d'une citation, on n'ajoute pas de start/end pour créer les éléments <sp> -->
<!--
        <xsl:when test="preceding-sibling::*[1][local-name()='start' and @type='cit']">
            <xsl:comment>pas d'ajout de milestone ici</xsl:comment>
        </xsl:when>
-->
        <xsl:when test="child::text:span[@text:style-name='TEI_speaker-inline']">
            <start type="sp"/>
        </xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_speaker']"></xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_didascaly'] and preceding-sibling::text:p[2][@text:style-name='TEI_speaker']"></xsl:when>
        <xsl:when test="parent::table:table-cell">
            <start type="sp"/>
        </xsl:when>
        <xsl:otherwise><start type="sp"/></xsl:otherwise>
    </xsl:choose>
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
    <xsl:choose>
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference'] and following-sibling::text:*[1][@text:style-name='TEI_bibl_start']"><end type="sp"/></xsl:when>
        
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference'] and not(following-sibling::text:*[1][@text:style-name='TEI_bibl_start'])"/>
        
        <xsl:when test="following-sibling::text:p[1][@text:style-name='TEI_replica'][child::text:span[@text:style-name='TEI_speaker-inline']]"><end type="sp"/></xsl:when>
        <xsl:when test="parent::table:table-cell">
            <end type="sp"/>
        </xsl:when>
        <xsl:otherwise><end type="sp"/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_bibl_reference']">
    <xsl:choose>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_versifiedreplica'] and not(preceding-sibling::text:*[1][@text:style-name='TEI_bibl_start'])">
            <xsl:copy-of select="."/>
            <end type="sp"/>
        </xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_replica'] and not(preceding-sibling::text:*[1][@text:style-name='TEI_bibl_start'])">
            <xsl:copy-of select="."/>
            <end type="sp"/>
        </xsl:when>
        <xsl:otherwise>
            <text:p text:style-name="TEI_bibl_reference">
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates/>
            </text:p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
</xsl:stylesheet>